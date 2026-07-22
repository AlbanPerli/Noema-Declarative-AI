from __future__ import annotations

from collections import OrderedDict
from concurrent.futures import ThreadPoolExecutor, as_completed
from contextvars import ContextVar
from dataclasses import dataclass, field
import inspect
from typing import Any, Callable

from .predicates import Predicate, ensure_predicate, label_of, value_of


_active_automaton = ContextVar("noema_active_automaton", default=None)
_active_state = ContextVar("noema_active_state", default=None)


@dataclass
class ValueRecord:
    label: str
    value: Any
    source: Any = None


@dataclass
class State:
    name: str
    actor: Any = None
    outputs: list[ValueRecord] = field(default_factory=list)
    status: str = "pending"
    action: Callable[..., Any] | None = None
    result: Any = None

    def record(self, value, label=None):
        record = ValueRecord(label or label_of(value), value_of(value), source=value)
        self.outputs.append(record)
        return value


@dataclass
class Transition:
    source: str
    target: str
    when: Predicate | Callable[[], bool] | bool | None = None
    label: str | None = None
    default: bool = False

    def matches(self, context=None):
        if self.default:
            return True
        if self.when is None:
            return True
        if callable(self.when) and not isinstance(self.when, Predicate):
            result = _call_with_optional_context(self.when, context)
            return ensure_predicate(result).evaluate()
        return ensure_predicate(self.when).evaluate()

    def display_label(self):
        if self.label:
            return self.label
        if self.default:
            return "default"
        if isinstance(self.when, Predicate):
            return self.when.label
        if callable(self.when):
            return getattr(self.when, "__name__", "condition")
        if self.when is None:
            return "always"
        return str(self.when)


@dataclass
class AutomatonResult:
    automaton: "Automaton"
    path: list[str]
    transitions: list[Transition]

    @property
    def outputs(self):
        values = []
        for state_name in self.path:
            state = self.automaton.states.get(state_name)
            if state is not None:
                values.extend(state.outputs)
        return values


class StateContext:
    def __init__(self, automaton, state):
        self.automaton = automaton
        self.state = state
        self._automaton_token = None
        self._state_token = None

    def __enter__(self):
        self.state.status = "running"
        self._automaton_token = _active_automaton.set(self.automaton)
        self._state_token = _active_state.set(self.state)
        return self.state

    def __exit__(self, exc_type, exc_value, traceback):
        self.state.status = "failed" if exc_type else "completed"
        _active_state.reset(self._state_token)
        _active_automaton.reset(self._automaton_token)
        return False

    def __call__(self, func):
        self.state.action = func
        return func


class BranchContext:
    def __init__(self, parallel_group, name, actor=None):
        self.parallel_group = parallel_group
        self.name = name
        self.actor = actor
        self.state_context = None

    def __enter__(self):
        state_name = self.parallel_group.branch_state_name(self.name)
        state = self.parallel_group.automaton._state(state_name, actor=self.actor)
        self.parallel_group.branches.setdefault(self.name, None)
        self.state_context = StateContext(self.parallel_group.automaton, state)
        return self.state_context.__enter__()

    def __exit__(self, exc_type, exc_value, traceback):
        return self.state_context.__exit__(exc_type, exc_value, traceback)


class ParallelGroup:
    def __init__(self, automaton, name, mode="sequential", max_workers=None):
        self.automaton = automaton
        self.name = name
        self.mode = mode
        self.max_workers = max_workers
        self.branches: OrderedDict[str, Callable[[], Any] | None] = OrderedDict()
        self.results = OrderedDict()

    def __enter__(self):
        self.automaton.parallel_groups[self.name] = self
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        return False

    def branch_state_name(self, branch_name):
        return f"{self.name}.{branch_name}"

    def branch(self, name, func=None, actor=None):
        if func is None:
            return BranchContext(self, name, actor=actor)
        self.add(name, func, actor=actor)
        return func

    def add(self, name, func, actor=None):
        self.branches[name] = func
        self.automaton._state(self.branch_state_name(name), actor=actor)
        return func

    def run(self, mode=None, max_workers=None):
        mode = mode or self.mode
        if mode == "threads":
            return self._run_threads(max_workers=max_workers or self.max_workers)
        return self._run_sequential()

    def _run_sequential(self):
        for name, func in self.branches.items():
            if func is None:
                continue
            state = self.automaton._state(self.branch_state_name(name))
            with StateContext(self.automaton, state):
                self.results[name] = func()
        return self.results

    def _run_threads(self, max_workers=None):
        callable_branches = {name: func for name, func in self.branches.items() if func is not None}
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            futures = {
                executor.submit(self._run_branch, name, func): name
                for name, func in callable_branches.items()
            }
            for future in as_completed(futures):
                self.results[futures[future]] = future.result()
        return self.results

    def _run_branch(self, name, func):
        state = self.automaton._state(self.branch_state_name(name))
        with StateContext(self.automaton, state):
            return func()


class Automaton:
    def __init__(self, name):
        self.name = name
        self.states: OrderedDict[str, State] = OrderedDict()
        self.transitions: list[Transition] = []
        self.parallel_groups: OrderedDict[str, ParallelGroup] = OrderedDict()
        self.data: OrderedDict[str, Any] = OrderedDict()
        self.last_result: AutomatonResult | None = None

    def _state(self, name, actor=None):
        name = _state_name(name)
        if name not in self.states:
            self.states[name] = State(name=name, actor=actor)
        elif actor is not None:
            self.states[name].actor = actor
        return self.states[name]

    def state(self, name, actor=None):
        return StateContext(self, self._state(name, actor=actor))

    def record(self, value, label=None, state=None):
        target_state = self._state(state) if state is not None else _active_state.get()
        if target_state is None:
            raise RuntimeError("Automaton.record() requires an active state or an explicit state name.")
        return target_state.record(value, label=label)

    def transition(self, source, target, when=None, label=None, default=False):
        transition = Transition(
            source=_state_name(source),
            target=_state_name(target),
            when=when,
            label=label,
            default=default,
        )
        self.transitions.append(transition)
        self._state(transition.source)
        self._state(transition.target)
        return transition

    def parallel(self, name, mode="sequential", max_workers=None):
        group = ParallelGroup(self, name, mode=mode, max_workers=max_workers)
        self.parallel_groups[name] = group
        return group

    def transitions_from(self, source):
        source = _state_name(source)
        return [transition for transition in self.transitions if transition.source == source]

    def next_transition(self, source):
        default_transition = None
        for transition in self.transitions_from(source):
            if transition.default:
                default_transition = transition
                continue
            if transition.matches(self.data):
                return transition
        return default_transition

    def run(self, start=None, max_steps=100, execute=True):
        if start is None:
            if not self.states:
                return AutomatonResult(self, [], [])
            current = next(iter(self.states))
        else:
            current = _state_name(start)

        path = [current]
        selected_transitions = []
        visited = set()

        for _ in range(max_steps):
            if execute:
                self._execute_state(current)
            transition = self.next_transition(current)
            if transition is None:
                break
            selected_transitions.append(transition)
            current = transition.target
            path.append(current)
            edge = (transition.source, transition.target)
            if edge in visited:
                break
            visited.add(edge)

        self.last_result = AutomatonResult(self, path, selected_transitions)
        return self.last_result

    def _execute_state(self, name):
        state = self._state(name)
        if state.status == "completed":
            return state.result
        if state.action is None:
            return state.result

        with StateContext(self, state):
            state.result = _call_with_optional_context(state.action, self.data)
            self.data[state.name] = state.result
        return state.result

    def to_mermaid(self):
        lines = ["flowchart TD"]
        for state in self.states.values():
            lines.append(f'  {self._node_id(state.name)}["{_escape(state.name)}"]')
        for transition in self.transitions:
            source = self._node_id(transition.source)
            target = self._node_id(transition.target)
            label = _escape(transition.display_label())
            lines.append(f"  {source} -->|{label}| {target}")
        return "\n".join(lines)

    def _node_id(self, name):
        sanitized = "".join(char if char.isalnum() else "_" for char in name)
        return f"state_{sanitized}"


def record_current_value(value, label=None):
    automaton = _active_automaton.get()
    state = _active_state.get()
    if automaton is None or state is None:
        return value
    return state.record(value, label=label)


def _state_name(state):
    if isinstance(state, State):
        return state.name
    return str(state)


def _escape(value):
    return str(value).replace('"', '\\"')


def _call_with_optional_context(func, context):
    parameters = inspect.signature(func).parameters
    if len(parameters) == 0:
        return func()
    return func(context)
