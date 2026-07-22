from __future__ import annotations

from dataclasses import dataclass
import inspect
from math import prod
from typing import Any, Callable, Iterable

from .predicates import Predicate, ensure_predicate, value_of


@dataclass(frozen=True)
class SelectGraphTransition:
    source: str
    target: str
    labels: tuple[str, ...]
    weight: float = 1.0
    when: Predicate | Callable[..., bool] | bool | None = None

    def matches(self, context):
        if self.when is None:
            return True
        if callable(self.when) and not isinstance(self.when, Predicate):
            return ensure_predicate(_call_with_optional_context(self.when, context)).evaluate()
        return ensure_predicate(self.when).evaluate()


@dataclass(frozen=True)
class SelectGraphStep:
    source: str
    target: str
    label: str
    weight: float
    transition: SelectGraphTransition


@dataclass
class SelectGraphResult:
    graph: "SelectGraph"
    steps: list[SelectGraphStep]

    @property
    def path(self):
        if not self.steps:
            return []
        return [self.steps[0].source] + [step.target for step in self.steps]

    @property
    def labels(self):
        return [step.label for step in self.steps]

    @property
    def text(self):
        return self.graph.separator.join(self.labels)

    @property
    def weight(self):
        if not self.steps:
            return 1.0
        return prod(step.weight for step in self.steps)


class SelectGraph:
    def __init__(self, name, separator=" "):
        self.name = name
        self.separator = separator
        self.transitions: list[SelectGraphTransition] = []
        self.last_result: SelectGraphResult | None = None

    def transition(self, source, target, labels: Iterable[str], weight=1.0, when=None):
        labels = tuple(str(label) for label in labels)
        if not labels:
            raise ValueError("SelectGraph.transition() requires at least one label.")
        transition = SelectGraphTransition(
            source=str(source),
            target=str(target),
            labels=labels,
            weight=float(weight),
            when=when,
        )
        self.transitions.append(transition)
        return transition

    edge = transition

    def transitions_from(self, source, context=None):
        context = context or {}
        source = str(source)
        return [
            transition
            for transition in self.transitions
            if transition.source == source and transition.matches(context)
        ]

    def run(self, start, objective=None, context=None, selector=None, max_steps=32, stop_states=None):
        context = dict(context or {})
        context.setdefault("choices", [])
        context.setdefault("path", [str(start)])
        context.setdefault("text", "")
        stop_states = {str(state) for state in (stop_states or {"end", "final", "stop"})}
        selector = selector or _default_selector

        current = str(start)
        steps = []
        for step_index in range(max_steps):
            if current in stop_states:
                break
            candidates = self._candidate_map(current, context)
            if not candidates:
                break

            prompt = self._build_prompt(
                state=current,
                candidates=candidates,
                objective=objective,
                context=context,
                step_index=step_index,
            )
            selected_label = str(value_of(_call_selector(selector, prompt, list(candidates), context)))
            if selected_label not in candidates:
                raise ValueError(
                    f"SelectGraph selector returned {selected_label!r}, "
                    f"expected one of {list(candidates)!r}."
                )

            transition = candidates[selected_label]
            step = SelectGraphStep(
                source=current,
                target=transition.target,
                label=selected_label,
                weight=transition.weight,
                transition=transition,
            )
            steps.append(step)
            current = transition.target
            context["choices"].append(selected_label)
            context["path"].append(current)
            context["text"] = self.separator.join(context["choices"])

        self.last_result = SelectGraphResult(self, steps)
        return self.last_result

    def _candidate_map(self, state, context):
        candidates = {}
        for transition in self.transitions_from(state, context=context):
            for label in transition.labels:
                if label in candidates:
                    raise ValueError(
                        f"Ambiguous SelectGraph label {label!r} from state {state!r}. "
                        "Outgoing labels must be unique."
                    )
                candidates[label] = transition
        return candidates

    def _build_prompt(self, state, candidates, objective, context, step_index):
        objective = objective or f"Choose the next transition for {self.name}."
        lines = [
            objective,
            f"Current state: {state}",
            f"Current text: {context.get('text', '')}",
            f"Step: {step_index + 1}",
            "Choose exactly one transition label.",
            "Weighted candidates:",
        ]
        for label, transition in candidates.items():
            lines.append(
                f"- {label} -> {transition.target} (weight: {transition.weight:g})"
            )
        return "\n".join(lines)

    def to_mermaid(self):
        lines = ["flowchart TD"]
        states = sorted({transition.source for transition in self.transitions} | {transition.target for transition in self.transitions})
        for state in states:
            lines.append(f'  {self._node_id(state)}["{_escape(state)}"]')
        for transition in self.transitions:
            label = ", ".join(transition.labels)
            label = f"{label} / w={transition.weight:g}"
            lines.append(
                f"  {self._node_id(transition.source)} -->|{_escape(label)}| "
                f"{self._node_id(transition.target)}"
            )
        return "\n".join(lines)

    def _node_id(self, name):
        sanitized = "".join(char if char.isalnum() else "_" for char in name)
        return f"select_{sanitized}"


def _default_selector(prompt, options, context=None):
    from .selectors import Select

    return Select(prompt, options=options).value


def _call_selector(selector, prompt, options, context):
    parameters = inspect.signature(selector).parameters
    parameter_count = len(parameters)
    if parameter_count == 1:
        return selector(options)
    if parameter_count == 2:
        return selector(prompt, options)
    return selector(prompt, options, context)


def _call_with_optional_context(func, context):
    parameters = inspect.signature(func).parameters
    if len(parameters) == 0:
        return func()
    return func(context)


def _escape(value):
    return str(value).replace('"', '\\"')


WeightedSelectGraph = SelectGraph
