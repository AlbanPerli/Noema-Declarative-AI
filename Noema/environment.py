from __future__ import annotations

import copy
import inspect
import json
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable

from guidance import gen, select

from .llm import LLM, current_runtime
from .predicates import value_of


@dataclass(frozen=True)
class ToolMetadata:
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class VisibleMetadata:
    name: str | None = None
    description: str | None = None


@dataclass(frozen=True)
class ToolSpec:
    name: str
    method_name: str
    signature: str
    description: str
    parameters: tuple[str, ...]


@dataclass
class EnvironmentObservation:
    tool: str
    args: dict[str, Any]
    result: Any


@dataclass
class EnvironmentDecision:
    tool: str | None = None
    args: dict[str, Any] = field(default_factory=dict)
    answer: str | None = None

    @classmethod
    def call(cls, tool_name: str, args: dict[str, Any] | None = None):
        return cls(tool=str(tool_name), args=dict(args or {}))

    @classmethod
    def final(cls, answer: Any):
        return cls(answer=str(value_of(answer)))

    @property
    def is_final(self):
        return self.tool is None


@dataclass
class EnvironmentRun:
    prompt: str
    observations: list[EnvironmentObservation] = field(default_factory=list)
    answer: str | None = None

    @property
    def value(self):
        return self.answer

    def __str__(self):
        return "" if self.answer is None else self.answer


class Memory:
    def __init__(self, default=None, *, default_factory=None, visible=True, description=None):
        if default is not None and default_factory is not None:
            raise ValueError("Memory accepts either default or default_factory, not both.")
        self.default = default
        self.default_factory = default_factory
        self.visible = visible
        self.description = description
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        values = instance.__dict__.setdefault("_noema_memory_values", {})
        if self.name not in values:
            values[self.name] = self._initial_value()
        return values[self.name]

    def __set__(self, instance, value):
        values = instance.__dict__.setdefault("_noema_memory_values", {})
        values[self.name] = value

    def _initial_value(self):
        if self.default_factory is not None:
            return self.default_factory()
        return copy.deepcopy(self.default)


class Visible(Memory):
    def __init__(self, default=None, *, default_factory=None, description=None):
        super().__init__(
            default=default,
            default_factory=default_factory,
            visible=True,
            description=description,
        )


def tool(func=None, *, name=None, description=None):
    def decorate(decorated):
        decorated.__noema_tool__ = ToolMetadata(name=name, description=description)
        return decorated

    if func is None:
        return decorate
    return decorate(func)


def visible(obj=None, *, name=None, description=None):
    def mark(decorated):
        if isinstance(decorated, property):
            return property(mark(decorated.fget), decorated.fset, decorated.fdel, decorated.__doc__)
        decorated.__noema_visible__ = VisibleMetadata(name=name, description=description)
        return decorated

    if obj is None:
        return mark
    if isinstance(obj, property):
        return property(mark(obj.fget), obj.fset, obj.fdel, obj.__doc__)
    return mark(obj)


class NoemaEnvironment:
    llm = None
    max_steps = 8
    max_tokens = 256
    argument_tokens = 128

    def __init__(self, llm=None, **state):
        if llm is not None:
            self.llm = llm
        self.last_run: EnvironmentRun | None = None
        for name, value in state.items():
            setattr(self, name, value)

    def __call__(
        self,
        prompt: str,
        *,
        max_steps: int | None = None,
        max_tokens: int | None = None,
        planner: Callable[..., Any] | None = None,
        return_run=False,
    ):
        max_steps = self.max_steps if max_steps is None else max_steps
        max_tokens = self.max_tokens if max_tokens is None else max_tokens
        if max_steps < 1:
            raise ValueError("NoemaEnvironment requires at least one execution step.")

        run = EnvironmentRun(prompt=str(prompt))
        self.last_run = run

        for step_index in range(max_steps):
            decision = self._decide(prompt, run, step_index, max_tokens, planner)
            if decision.is_final:
                run.answer = decision.answer or ""
                return run if return_run else run.answer

            observation = self.invoke(decision.tool, **decision.args)
            run.observations.append(observation)

        raise RuntimeError("NoemaEnvironment reached max_steps without a final answer.")

    def invoke(self, tool_name: str, **kwargs):
        specs = self.tool_specs()
        if tool_name not in specs:
            raise ValueError(f"Unknown Noema environment tool: {tool_name!r}.")
        spec = specs[tool_name]
        method = getattr(self, spec.method_name)
        inspect.signature(method).bind(**kwargs)
        result = method(**kwargs)
        return EnvironmentObservation(tool=tool_name, args=dict(kwargs), result=result)

    def manifest(self):
        return {
            "environment": type(self).__name__,
            "description": inspect.getdoc(type(self)) or "",
            "state": self.visible_state(),
            "tools": [
                {
                    "name": spec.name,
                    "signature": spec.signature,
                    "description": spec.description,
                    "parameters": list(spec.parameters),
                }
                for spec in self.tool_specs().values()
            ],
        }

    def visible_state(self):
        state = {}
        for name, declaration in self._memory_declarations().items():
            if declaration.visible:
                state[name] = _json_safe(getattr(self, name))

        for name, member in self._visible_declarations().items():
            exposed_name = _visible_name(name, member)
            try:
                state[exposed_name] = _json_safe(_read_visible_member(self, name, member))
            except Exception as error:
                state[exposed_name] = f"<error: {error}>"

        return state

    def tool_specs(self):
        specs = {}
        for method_name, member in self._tool_declarations().items():
            metadata = member.__noema_tool__
            tool_name = metadata.name or method_name
            if tool_name in specs:
                raise ValueError(f"Duplicate Noema environment tool name: {tool_name!r}.")
            bound_method = getattr(self, method_name)
            signature = inspect.signature(bound_method)
            specs[tool_name] = ToolSpec(
                name=tool_name,
                method_name=method_name,
                signature=f"{tool_name}{signature}",
                description=metadata.description or inspect.getdoc(bound_method) or "",
                parameters=tuple(signature.parameters),
            )
        return specs

    def describe(self):
        manifest = self.manifest()
        lines = [
            f"Environment: {manifest['environment']}",
        ]
        if manifest["description"]:
            lines.append(f"Description: {manifest['description']}")

        lines.append("Visible state:")
        if manifest["state"]:
            for key, value in manifest["state"].items():
                lines.append(f"- {key}: {json.dumps(value, ensure_ascii=True)}")
        else:
            lines.append("- none")

        lines.append("Available tools:")
        if manifest["tools"]:
            for spec in manifest["tools"]:
                description = f" - {spec['description']}" if spec["description"] else ""
                lines.append(f"- {spec['signature']}{description}")
        else:
            lines.append("- none")
        return "\n".join(lines)

    def _decide(self, prompt, run, step_index, max_tokens, planner):
        if planner is not None:
            return _normalize_decision(_call_planner(planner, self, prompt, run))
        return self._llm_decision(prompt, run, step_index, max_tokens)

    def _llm_decision(self, prompt, run, step_index, max_tokens):
        runtime = self._activate_runtime()
        specs = self.tool_specs()
        action_options = ["final"] + [f"tool:{name}" for name in specs]
        action_name = f"noema_environment_action_{step_index}"

        llm = runtime.llm
        llm += self._decision_prompt(prompt, run)
        llm += f"\n#NOEMA_ENV_ACTION_{step_index}: "
        llm += select(action_options, name=action_name) + "\n"
        action = llm[action_name]

        if action == "final":
            answer_name = f"noema_environment_final_{step_index}"
            llm += runtime.reasoning_prelude()
            llm += f"#NOEMA_ENV_FINAL_{step_index}: "
            llm += gen(name=answer_name, **runtime.generation_kwargs(max_tokens)) + "\n"
            runtime.llm = llm
            return EnvironmentDecision.final(llm[answer_name])

        tool_name = action.split(":", 1)[1]
        spec = specs[tool_name]
        args = {}
        if spec.parameters:
            args_name = f"noema_environment_args_{step_index}"
            llm += self._argument_prompt(spec)
            llm += f"\n#NOEMA_ENV_ARGS_JSON_{step_index}: "
            llm += gen(
                name=args_name,
                regex=r"\{[^\n]*\}",
                **runtime.generation_kwargs(self.argument_tokens),
            ) + "\n"
            args = _parse_json_object(llm[args_name])

        runtime.llm = llm
        return EnvironmentDecision.call(tool_name, args)

    def _decision_prompt(self, prompt, run):
        return textwrap.dedent(
            f"""
            NOEMA ENVIRONMENT EXECUTION
            You are executing inside this Python object. You may inspect visible
            state, call one exposed tool, or produce the final answer. Choose a
            tool only when its result is needed.

            USER PROMPT:
            {prompt}

            {self.describe()}

            OBSERVATIONS:
            {_format_observations(run.observations)}

            Choose the next action.
            """
        ).strip()

    def _argument_prompt(self, spec):
        return textwrap.dedent(
            f"""
            Build arguments for tool {spec.name}.
            Required JSON object parameters: {', '.join(spec.parameters)}.
            Return a compact one-line JSON object only.
            """
        ).strip()

    def _activate_runtime(self):
        llm = getattr(self, "llm", None)
        if isinstance(llm, LLM):
            return llm.activate()
        if llm is not None:
            return LLM(llm).activate()
        return current_runtime()

    @classmethod
    def _memory_declarations(cls):
        declarations = {}
        for klass in reversed(cls.__mro__):
            for name, member in vars(klass).items():
                if isinstance(member, Memory):
                    declarations[name] = member
        return declarations

    @classmethod
    def _visible_declarations(cls):
        declarations = {}
        for klass in reversed(cls.__mro__):
            for name, member in vars(klass).items():
                if isinstance(member, Memory):
                    continue
                target = member.fget if isinstance(member, property) else member
                if getattr(target, "__noema_visible__", None) is not None:
                    declarations[name] = member
        return declarations

    @classmethod
    def _tool_declarations(cls):
        declarations = {}
        for klass in reversed(cls.__mro__):
            for name, member in vars(klass).items():
                if getattr(member, "__noema_tool__", None) is not None:
                    declarations[name] = member
        return declarations


def _normalize_decision(decision):
    if isinstance(decision, EnvironmentDecision):
        return decision
    if isinstance(decision, str):
        return EnvironmentDecision.final(decision)
    if isinstance(decision, dict):
        if "answer" in decision:
            return EnvironmentDecision.final(decision["answer"])
        if "final" in decision:
            return EnvironmentDecision.final(decision["final"])
        if "tool" in decision:
            return EnvironmentDecision.call(decision["tool"], decision.get("args"))
    raise TypeError("Planner must return an EnvironmentDecision, a final string, or a decision dict.")


def _call_planner(planner, environment, prompt, run):
    parameter_count = len(inspect.signature(planner).parameters)
    if parameter_count == 1:
        return planner(environment)
    if parameter_count == 2:
        return planner(environment, prompt)
    return planner(environment, prompt, run)


def _visible_name(default_name, member):
    target = member.fget if isinstance(member, property) else member
    metadata = target.__noema_visible__
    return metadata.name or default_name


def _read_visible_member(instance, name, member):
    if isinstance(member, property):
        return getattr(instance, name)
    bound = getattr(instance, name)
    if len(inspect.signature(bound).parameters) == 0:
        return bound()
    return f"<callable {inspect.signature(bound)}>"


def _format_observations(observations):
    if not observations:
        return "- none"
    lines = []
    for observation in observations:
        payload = {
            "tool": observation.tool,
            "args": observation.args,
            "result": _json_safe(observation.result),
        }
        lines.append(f"- {json.dumps(payload, ensure_ascii=True)}")
    return "\n".join(lines)


def _parse_json_object(value):
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"NoemaEnvironment expected JSON object arguments, got: {value!r}") from error
    if not isinstance(parsed, dict):
        raise ValueError(f"NoemaEnvironment expected JSON object arguments, got: {value!r}")
    return parsed


def _json_safe(value):
    value = value_of(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)
