from __future__ import annotations

import ast
import copy
import inspect
import json
import re
import textwrap
from dataclasses import MISSING, asdict, dataclass, field, fields, is_dataclass
from typing import Any, Callable, get_args, get_origin, get_type_hints, is_typeddict

from guidance import gen, select

from .llm import LLM, current_runtime
from .predicates import value_of


_YELLOW = "\033[93m"
_BLUE = "\033[94m"
_RESET = "\033[0m"


@dataclass(frozen=True)
class ToolMetadata:
    name: str | None = None
    description: str | None = None
    argument_schema: Any = None
    result_schema: Any = None


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
    component_name: str | None = None
    local_name: str | None = None
    parameter_annotations: dict[str, Any] = field(default_factory=dict)
    return_annotation: Any = inspect.Signature.empty
    argument_schema: Any = None
    result_schema: Any = None

    @property
    def is_component_tool(self):
        return self.component_name is not None


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
    observation: EnvironmentObservation | None = None

    @classmethod
    def call(cls, tool_name: str, args: dict[str, Any] | None = None):
        return cls(tool=str(tool_name), args=dict(args or {}))

    @classmethod
    def final(cls, answer: Any):
        return cls(answer=str(value_of(answer)))

    @classmethod
    def observed(cls, observation: EnvironmentObservation):
        return cls(tool=observation.tool, args=dict(observation.args), observation=observation)

    @property
    def is_final(self):
        return self.tool is None and self.observation is None


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


class Component:
    def __init__(self, component=None, *args, description=None, **kwargs):
        self.component = component
        self.args = args
        self.kwargs = kwargs
        self.description = description
        self.name = None

    def __set_name__(self, owner, name):
        self.name = name

    def __get__(self, instance, owner):
        if instance is None:
            return self
        values = instance.__dict__.setdefault("_noema_component_values", {})
        if self.name not in values:
            values[self.name] = self._initial_value(instance)
        return values[self.name]

    def __set__(self, instance, value):
        self._validate_component(value)
        values = instance.__dict__.setdefault("_noema_component_values", {})
        values[self.name] = value

    def _initial_value(self, owner):
        if self.component is None:
            raise AttributeError(f"Noema component {self.name!r} has not been assigned.")
        if isinstance(self.component, type):
            component = self.component(*self.args, **self.kwargs)
        elif callable(self.component) and not isinstance(self.component, NoemaEnvironment):
            component = _call_component_factory(self.component, owner)
        else:
            component = self.component
        self._validate_component(component)
        if getattr(component, "llm", None) is None and getattr(owner, "llm", None) is not None:
            component.llm = owner.llm
        return component

    def _validate_component(self, component):
        if not isinstance(component, NoemaEnvironment):
            raise TypeError("Noema Component values must be NoemaEnvironment instances.")


def tool(
    func=None,
    *,
    name=None,
    description=None,
    args=None,
    returns=None,
    argument_schema=None,
    result_schema=None,
):
    def decorate(decorated):
        decorated.__noema_tool__ = ToolMetadata(
            name=name,
            description=description,
            argument_schema=_single_schema(
                "args",
                args,
                "argument_schema",
                argument_schema,
            ),
            result_schema=_single_schema(
                "returns",
                returns,
                "result_schema",
                result_schema,
            ),
        )
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
    argument_tokens = 256
    tool_argument_schemas: dict[str, Any] = {}
    tool_result_schemas: dict[str, Any] = {}
    final_retry_tokens = 96
    final_stop_sequences = (
        "\n***",
        "\n*Self-Correction",
        "\nSelf-Correction",
        "\nFinal Response Generation",
        "\nFinal response generation",
        "\nFinal Response Mode",
        "\nFinal response mode",
        "\nFinal Answer Generation",
        "\nFinal answer generation",
        "\nOutputting Final Answer",
        "\nOutputting final answer",
        "\nPlan:",
        "\nplan:",
        "\nWait",
        "\nwait",
        "\nThe execution sequence",
        "\nthe execution sequence",
        "\nThe chosen output format",
        "\n#NOEMA_ENV",
    )

    def __init__(self, llm=None, **state):
        if llm is not None:
            self.llm = llm
        self.last_run: EnvironmentRun | None = None
        self._noema_environment_verbose = False
        self._noema_dynamic_tool_argument_schemas: dict[str, Any] = {}
        self._noema_dynamic_tool_result_schemas: dict[str, Any] = {}
        for name, value in state.items():
            setattr(self, name, value)

    def set_tool_schema(self, tool_name, *, args=None, returns=None):
        if args is not None:
            self._noema_dynamic_tool_argument_schemas[str(tool_name)] = copy.deepcopy(args)
        if returns is not None:
            self._noema_dynamic_tool_result_schemas[str(tool_name)] = copy.deepcopy(returns)
        return self

    def clear_tool_schema(self, tool_name=None):
        if tool_name is None:
            self._noema_dynamic_tool_argument_schemas.clear()
            self._noema_dynamic_tool_result_schemas.clear()
            return self

        self._noema_dynamic_tool_argument_schemas.pop(str(tool_name), None)
        self._noema_dynamic_tool_result_schemas.pop(str(tool_name), None)
        return self

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
        self._noema_environment_verbose = False

        for step_index in range(max_steps):
            decision = self._decide(prompt, run, step_index, max_tokens, planner)
            if decision.is_final:
                run.answer = _clean_final_answer(decision.answer or "")
                self._log_final(step_index, run.answer)
                return run if return_run else run.answer

            if decision.observation is not None:
                observation = decision.observation
            else:
                observation = self.invoke(decision.tool, **decision.args)
            run.observations.append(observation)
            self._log_observation(step_index, observation)

        raise RuntimeError("NoemaEnvironment reached max_steps without a final answer.")

    def invoke(self, tool_name: str, **kwargs):
        specs = self.available_tool_specs()
        if tool_name not in specs:
            raise ValueError(f"Unknown Noema environment tool: {tool_name!r}.")
        spec = specs[tool_name]
        if spec.is_component_tool:
            component = getattr(self, spec.component_name)
            observation = component.invoke(spec.local_name, **kwargs)
            result = observation.result
            try:
                result = _normalize_tool_result(
                    result,
                    self.tool_result_schema(tool_name, spec),
                )
            except (TypeError, ValueError) as error:
                result = _tool_result_error(spec, result, error)
            return EnvironmentObservation(tool=tool_name, args=dict(kwargs), result=result)

        method = getattr(self, spec.method_name)
        signature = inspect.signature(method)
        try:
            kwargs = _coerce_tool_arguments(spec, kwargs)
            signature.bind(**kwargs)
        except TypeError as error:
            return EnvironmentObservation(
                tool=tool_name,
                args=dict(kwargs),
                result=_tool_argument_error(spec, kwargs, error),
            )
        result = method(**kwargs)
        try:
            result = _normalize_tool_result(
                result,
                self.tool_result_schema(tool_name, spec),
            )
        except (TypeError, ValueError) as error:
            result = _tool_result_error(spec, result, error)
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
                    "argument_schema": _json_safe(_safe_schema(lambda: self.tool_argument_schema(spec.name, spec))),
                    "result_schema": _json_safe(_safe_schema(lambda: self.tool_result_schema(spec.name, spec))),
                }
                for spec in self.tool_specs().values()
            ],
            "components": self.component_specs(),
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
            type_hints = _type_hints(bound_method)
            specs[tool_name] = ToolSpec(
                name=tool_name,
                method_name=method_name,
                signature=f"{tool_name}{signature}",
                description=metadata.description or inspect.getdoc(bound_method) or "",
                parameters=tuple(signature.parameters),
                parameter_annotations={
                    name: type_hints.get(name, parameter.annotation)
                    for name, parameter in signature.parameters.items()
                },
                return_annotation=type_hints.get("return", signature.return_annotation),
                argument_schema=metadata.argument_schema,
                result_schema=metadata.result_schema,
            )
        return specs

    def available_tool_specs(self):
        specs = dict(self.tool_specs())
        for component_name, component in self.components().items():
            for local_name, child_spec in component.available_tool_specs().items():
                tool_name = f"{component_name}.{local_name}"
                if tool_name in specs:
                    raise ValueError(f"Duplicate Noema environment tool name: {tool_name!r}.")
                specs[tool_name] = ToolSpec(
                    name=tool_name,
                    method_name=child_spec.method_name,
                    signature=f"{component_name}.{child_spec.signature}",
                    description=child_spec.description,
                    parameters=child_spec.parameters,
                    component_name=component_name,
                    local_name=local_name,
                    parameter_annotations=child_spec.parameter_annotations,
                    return_annotation=child_spec.return_annotation,
                    argument_schema=child_spec.argument_schema,
                    result_schema=child_spec.result_schema,
                )
        return specs

    def components(self):
        components = {}
        for name in self._component_declarations():
            try:
                components[name] = getattr(self, name)
            except AttributeError:
                continue
        return components

    def component_specs(self):
        specs = []
        declarations = self._component_declarations()
        for name, component in self.components().items():
            declaration = declarations[name]
            tools = []
            for local_name, tool_spec in component.available_tool_specs().items():
                tools.append({
                    "name": f"{name}.{local_name}",
                    "signature": f"{name}.{tool_spec.signature}",
                    "description": tool_spec.description,
                    "parameters": list(tool_spec.parameters),
                    "argument_schema": _json_safe(_safe_schema(lambda spec=tool_spec: component.tool_argument_schema(local_name, spec))),
                    "result_schema": _json_safe(_safe_schema(lambda spec=tool_spec: component.tool_result_schema(local_name, spec))),
                })
            specs.append({
                "name": name,
                "environment": type(component).__name__,
                "description": declaration.description or inspect.getdoc(type(component)) or "",
                "state": component.visible_state(),
                "tools": tools,
            })
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

        lines.append("Components:")
        if manifest["components"]:
            for component in manifest["components"]:
                description = f" - {component['description']}" if component["description"] else ""
                lines.append(f"- {component['name']}: {component['environment']}{description}")
                if component["state"]:
                    for key, value in component["state"].items():
                        lines.append(f"  state.{key}: {json.dumps(value, ensure_ascii=True)}")
                for spec in component["tools"]:
                    tool_description = f" - {spec['description']}" if spec["description"] else ""
                    lines.append(f"  tool {spec['signature']}{tool_description}")
        else:
            lines.append("- none")

        lines.append("Available tools:")
        available_tools = self.available_tool_specs()
        if available_tools:
            for spec in available_tools.values():
                description = f" - {spec.description}" if spec.description else ""
                lines.append(f"- {spec.signature}{description}")
        else:
            lines.append("- none")
        return "\n".join(lines)

    def _decide(self, prompt, run, step_index, max_tokens, planner):
        if planner is not None:
            return _normalize_decision(_call_planner(planner, self, prompt, run))
        return self._llm_decision(prompt, run, step_index, max_tokens)

    def _llm_decision(self, prompt, run, step_index, max_tokens):
        runtime = self._activate_runtime()
        self._noema_environment_verbose = bool(getattr(runtime, "verbose", False))
        specs = self.available_tool_specs()
        action_options = ["final"] + [f"tool:{name}" for name in specs]
        action_name = f"noema_environment_action_{step_index}"

        llm = runtime.llm
        llm += self._decision_prompt(prompt, run)
        llm += f"\n#NOEMA_ENV_ACTION_{step_index}: "
        llm += select(action_options, name=action_name) + "\n"
        action = llm[action_name]
        self._log_action(step_index, action, action_options)

        if action == "final":
            answer_name = f"noema_environment_final_{step_index}"
            llm += self._final_prompt(prompt, run)
            generation_kwargs = runtime.generation_kwargs(max_tokens)
            generation_kwargs["stop"] = list(self.final_stop_sequences)
            llm += runtime.reasoning_prelude()
            llm += f"#NOEMA_ENV_FINAL_{step_index}: "
            llm += gen(name=answer_name, **generation_kwargs) + "\n"
            raw_answer = llm[answer_name]
            if not _clean_final_answer(raw_answer) and str(raw_answer).strip():
                retry_name = f"noema_environment_final_retry_{step_index}"
                retry_kwargs = runtime.generation_kwargs(min(max_tokens, self.final_retry_tokens))
                retry_kwargs["stop"] = list(self.final_stop_sequences)
                llm += self._final_retry_prompt(prompt, run)
                llm += runtime.reasoning_prelude()
                llm += f"#NOEMA_ENV_FINAL_RETRY_{step_index}: "
                llm += gen(name=retry_name, **retry_kwargs) + "\n"
                raw_answer = llm[retry_name]
            runtime.llm = llm
            return EnvironmentDecision.final(raw_answer)

        tool_name = action.split(":", 1)[1]
        spec = specs[tool_name]
        args = {}
        if spec.parameters:
            try:
                schema = self.tool_argument_schema(tool_name, spec)
                args = _generate_tool_arguments_from_schema(
                    spec=spec,
                    schema=schema,
                    step_index=step_index,
                    max_tokens=max_tokens,
                )
            except (TypeError, ValueError) as error:
                runtime.llm = runtime.llm
                return EnvironmentDecision.observed(
                    EnvironmentObservation(
                        tool=tool_name,
                        args={},
                        result=_tool_argument_schema_error(spec, error),
                    )
                )
            llm = runtime.llm
            self._log_arguments(step_index, spec, args)

        runtime.llm = llm
        return EnvironmentDecision.call(tool_name, args)

    def _decision_prompt(self, prompt, run):
        return textwrap.dedent(
            f"""
            NOEMA ENVIRONMENT EXECUTION
            You are executing inside this Python object. You may inspect visible
            state, call one exposed tool, or produce the final answer. Choose a
            tool only when its result is needed.
            If the latest observation is an error, correct the failed tool call
            before producing a final answer.

            USER PROMPT:
            {prompt}

            {self.describe()}

            OBSERVATIONS:
            {_format_observations(run.observations)}

            Choose the next action.
            """
        ).strip()

    def _final_prompt(self, prompt, run):
        return textwrap.dedent(
            f"""
            Write the user-facing answer now.
            Use the executed tool results as facts, but do not name tools,
            actions, observations, planning, instructions, or output rules.
            Keep the answer short and direct unless the request asks otherwise.
            Do not write labels, headings, analysis, self-corrections, plans,
            or <think> blocks.

            Original request:
            {prompt}

            Facts from executed tools:
            {_format_observations(run.observations)}
            """
        ).strip() + "\n"

    def _final_retry_prompt(self, prompt, run):
        return textwrap.dedent(
            f"""
            The previous output was rejected because it was meta commentary
            instead of the answer. Reply with one short user-facing answer.
            Start immediately with the answer content.

            Original request:
            {prompt}

            Facts from executed tools:
            {_format_observations(run.observations)}
            """
        ).strip() + "\n"

    def _argument_prompt(self, spec):
        return textwrap.dedent(
            f"""
            Build arguments for tool {spec.name}.
            Tool signature: {spec.signature}.
            Required JSON object keys: {', '.join(spec.parameters)}.
            JSON shape: {_argument_json_shape(spec)}.
            Include every required key exactly once.
            Use double quotes for every key and string value.
            Do not use Python dict syntax, single quotes, comments, ellipses,
            placeholders, or trailing commas.
            Return a compact one-line JSON object only.
            """
        ).strip()

    def tool_argument_schema(self, tool_name, spec):
        schema = self._tool_schema(
            tool_name,
            spec,
            dynamic_attribute="_noema_dynamic_tool_argument_schemas",
            class_attribute="tool_argument_schemas",
            metadata_attribute="argument_schema",
        )
        if schema is None:
            schema = _argument_schema_from_spec(spec)
        return copy.deepcopy(schema)

    def tool_result_schema(self, tool_name, spec):
        schema = self._tool_schema(
            tool_name,
            spec,
            dynamic_attribute="_noema_dynamic_tool_result_schemas",
            class_attribute="tool_result_schemas",
            metadata_attribute="result_schema",
        )
        if schema is None:
            schema = _result_schema_from_spec(spec)
        return copy.deepcopy(schema)

    def _tool_schema(self, tool_name, spec, *, dynamic_attribute, class_attribute, metadata_attribute):
        dynamic_schemas = getattr(self, dynamic_attribute, {})
        if tool_name in dynamic_schemas:
            return _resolve_schema(dynamic_schemas[tool_name], self, spec)
        if spec.local_name in dynamic_schemas:
            return _resolve_schema(dynamic_schemas[spec.local_name], self, spec)

        metadata_schema = _resolve_schema(getattr(spec, metadata_attribute), self, spec)
        if metadata_schema is not None:
            return metadata_schema

        class_schemas = self._tool_schema_declarations(class_attribute)
        if tool_name in class_schemas:
            return _resolve_schema(class_schemas[tool_name], self, spec)
        if spec.local_name in class_schemas:
            return _resolve_schema(class_schemas[spec.local_name], self, spec)
        return None

    def _activate_runtime(self):
        llm = getattr(self, "llm", None)
        if isinstance(llm, LLM):
            return llm.activate()
        if llm is not None:
            return LLM(llm).activate()
        return current_runtime()

    def _log_action(self, step_index, action, options):
        if not self._noema_environment_verbose:
            return
        print(
            f"NOEMA_ENV_ACTION_{step_index} = {_YELLOW}{action}{_RESET} "
            f"({_BLUE}Choose next environment action : {options}{_RESET})"
        )

    def _log_arguments(self, step_index, spec, args):
        if not self._noema_environment_verbose:
            return
        print(
            f"NOEMA_ENV_ARGS_{step_index} = {_YELLOW}{_json_log(args)}{_RESET} "
            f"({_BLUE}Build arguments for {spec.signature}{_RESET})"
        )

    def _log_observation(self, step_index, observation):
        if not self._noema_environment_verbose:
            return
        print(
            f"NOEMA_ENV_OBSERVATION_{step_index} = {_YELLOW}{_json_log(observation.result)}{_RESET} "
            f"({_BLUE}{_format_tool_call(observation.tool, observation.args)}{_RESET})"
        )

    def _log_final(self, step_index, answer):
        if not self._noema_environment_verbose:
            return
        print(
            f"NOEMA_ENV_FINAL_{step_index} = {_YELLOW}{answer}{_RESET} "
            f"({_BLUE}Final environment response{_RESET})"
        )

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
    def _component_declarations(cls):
        declarations = {}
        for klass in reversed(cls.__mro__):
            for name, member in vars(klass).items():
                if isinstance(member, Component):
                    declarations[name] = member
        return declarations

    @classmethod
    def _tool_schema_declarations(cls, attribute):
        declarations = {}
        for klass in reversed(cls.__mro__):
            values = getattr(klass, attribute, None)
            if values:
                declarations.update(values)
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


def _single_schema(primary_name, primary, alias_name, alias):
    if primary is not None and alias is not None:
        raise ValueError(f"Use either {primary_name!r} or {alias_name!r}, not both.")
    if primary is not None:
        return primary
    return alias


def _resolve_schema(schema, owner, spec):
    if schema is None:
        return None
    if isinstance(schema, dict):
        return {
            str(key): _resolve_schema(value, owner, spec)
            for key, value in schema.items()
        }
    if isinstance(schema, list):
        return [
            _resolve_schema(value, owner, spec)
            for value in schema
        ]
    if inspect.isclass(schema) or not callable(schema):
        return schema

    try:
        signature = inspect.signature(schema)
    except (TypeError, ValueError):
        return _resolve_schema(schema(owner, spec), owner, spec)

    for candidate_args in ((owner, spec), (owner,), ()):
        try:
            signature.bind(*candidate_args)
        except TypeError:
            continue
        return _resolve_schema(schema(*candidate_args), owner, spec)

    raise TypeError(f"Cannot call dynamic schema factory for tool {spec.name!r}.")


def _safe_schema(resolver):
    try:
        return resolver()
    except (TypeError, ValueError) as error:
        return {
            "error": {
                "type": "invalid_tool_schema",
                "message": str(error),
            }
        }


def _type_hints(callable_object):
    try:
        return get_type_hints(callable_object)
    except Exception:
        return {}


def _call_component_factory(factory, owner):
    try:
        parameters = inspect.signature(factory).parameters
    except (TypeError, ValueError):
        return factory()
    if len(parameters) == 0:
        return factory()
    return factory(owner)


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


def _format_tool_call(tool_name, args):
    if not args:
        return f"{tool_name}()"
    arguments = ", ".join(f"{name}={value!r}" for name, value in args.items())
    return f"{tool_name}({arguments})"


def _argument_schema_from_spec(spec):
    schema = {}
    for parameter in spec.parameters:
        schema[parameter] = _schema_from_annotation(
            parameter,
            spec.parameter_annotations.get(parameter, inspect.Signature.empty),
            allow_unconstrained_dict=False,
        )
    return schema


def _result_schema_from_spec(spec):
    if spec.return_annotation is inspect.Signature.empty:
        return None
    return _schema_from_annotation(
        "return",
        spec.return_annotation,
        allow_unconstrained_dict=True,
    )


def _schema_from_annotation(parameter, annotation, *, allow_unconstrained_dict):
    if _is_any_annotation(annotation):
        return {"type": "object"} if allow_unconstrained_dict else "string"

    typed_dict_schema = _typed_dict_schema(annotation)
    if typed_dict_schema is not None:
        return typed_dict_schema

    model_schema = _model_json_schema(annotation)
    if model_schema is not None:
        return model_schema

    dataclass_schema = _dataclass_schema(annotation)
    if dataclass_schema is not None:
        return dataclass_schema

    literal_options = _literal_options(annotation)
    if literal_options:
        return {
            "type": "string",
            "enum": [str(option) for option in literal_options],
        }

    if _is_str_annotation(annotation):
        return "string"
    if _is_bool_annotation(annotation):
        return True
    if _is_int_annotation(annotation):
        return 0
    if _is_float_annotation(annotation):
        return 0.0
    if _is_list_annotation(annotation):
        return [_list_item_schema(parameter, annotation, allow_unconstrained_dict)]
    if _is_dict_annotation(annotation):
        if allow_unconstrained_dict:
            return {"type": "object"}
        raise TypeError(
            f"Tool parameter {parameter!r} is a dict and requires a declared argument schema."
        )
    return "string"


def _typed_dict_schema(annotation):
    try:
        is_typed_dict = is_typeddict(annotation)
    except TypeError:
        is_typed_dict = False
    if not is_typed_dict:
        return None

    annotations = get_type_hints(annotation)
    required_keys = getattr(annotation, "__required_keys__", set(annotations))
    return {
        "type": "object",
        "properties": {
            str(key): _to_json_schema(
                _schema_from_annotation(
                    str(key),
                    value,
                    allow_unconstrained_dict=True,
                ),
                path=str(key),
            )
            for key, value in annotations.items()
        },
        "required": [str(key) for key in required_keys],
        "additionalProperties": False,
    }


def _model_json_schema(annotation):
    if not inspect.isclass(annotation):
        return None
    if hasattr(annotation, "model_json_schema"):
        return annotation.model_json_schema()
    if hasattr(annotation, "schema"):
        return annotation.schema()
    return None


def _dataclass_schema(annotation):
    if not inspect.isclass(annotation) or not is_dataclass(annotation):
        return None

    type_hints = _type_hints(annotation)
    return {
        "type": "object",
        "properties": {
            field.name: _to_json_schema(
                _schema_from_annotation(
                    field.name,
                    type_hints.get(field.name, field.type),
                    allow_unconstrained_dict=True,
                ),
                path=field.name,
            )
            for field in fields(annotation)
        },
        "required": [field.name for field in fields(annotation) if _dataclass_field_is_required(field)],
        "additionalProperties": False,
    }


def _dataclass_field_is_required(field):
    return (
        field.default is MISSING
        and getattr(field, "default_factory", MISSING) is MISSING
    )


def _literal_options(annotation):
    origin = get_origin(annotation)
    if _annotation_source(origin).endswith("Literal"):
        return list(get_args(annotation))

    source = _annotation_source(annotation)
    lower = source.lower()
    marker = "literal["
    index = lower.find(marker)
    if index < 0 or not source.endswith("]"):
        return []

    inner = source[index + len(marker):-1]
    try:
        parsed = ast.literal_eval(f"({inner},)")
    except (SyntaxError, ValueError):
        return []
    return list(parsed)


def _list_item_schema(parameter, annotation, allow_unconstrained_dict):
    args = get_args(annotation)
    if args:
        return _schema_from_annotation(
            f"{parameter} item",
            args[0],
            allow_unconstrained_dict=allow_unconstrained_dict,
        )

    source = _annotation_source(annotation)
    lower = source.lower()
    for prefix in ("list[", "typing.list["):
        if lower.startswith(prefix) and source.endswith("]"):
            inner = source[len(prefix):-1]
            return _schema_from_annotation(
                f"{parameter} item",
                inner,
                allow_unconstrained_dict=allow_unconstrained_dict,
            )

    return "string"


def _generate_tool_arguments_from_schema(spec, schema, step_index, max_tokens):
    if not isinstance(schema, dict):
        raise TypeError("Tool argument schema must be a dict.")

    argument_schema = _normalize_argument_schema(spec, schema)
    json_schema = _tool_arguments_json_schema(spec, argument_schema)

    from .json_gen import JsonObject

    generator = JsonObject(
        None,
        schema=json_schema,
        var=_schema_var_name(step_index, f"{spec.name}.arguments"),
        max_tokens=max(64, max_tokens),
    )
    generator.value = _schema_argument_prompt(spec, argument_schema, json_schema)
    generator.execute(max_tokens=max(64, max_tokens))

    return _normalize_tool_arguments(spec, generator.value)


def _normalize_argument_schema(spec, schema):
    if not isinstance(schema, dict):
        raise TypeError("Tool argument schema must be a dict.")

    if len(spec.parameters) == 1:
        parameter = spec.parameters[0]
        if parameter not in schema and _is_dict_annotation(spec.parameter_annotations.get(parameter)):
            return {parameter: schema}

    argument_schema = dict(schema)
    for parameter in spec.parameters:
        if parameter not in argument_schema:
            argument_schema[parameter] = _schema_from_annotation(
                parameter,
                spec.parameter_annotations.get(parameter, inspect.Signature.empty),
                allow_unconstrained_dict=False,
            )

    return {
        parameter: argument_schema[parameter]
        for parameter in spec.parameters
    }


def _tool_arguments_json_schema(spec, argument_schema):
    return {
        "type": "object",
        "properties": {
            parameter: _to_json_schema(
                argument_schema[parameter],
                path=f"{spec.name}.{parameter}",
            )
            for parameter in spec.parameters
        },
        "required": list(spec.parameters),
        "additionalProperties": False,
    }


def _to_json_schema(schema, path):
    if _looks_like_json_schema(schema):
        return copy.deepcopy(schema)

    if isinstance(schema, dict):
        return {
            "type": "object",
            "properties": {
                str(key): _to_json_schema(value, path=f"{path}.{key}")
                for key, value in schema.items()
            },
            "required": [str(key) for key in schema],
            "additionalProperties": False,
        }

    if isinstance(schema, list):
        item_schema = schema[0] if schema else "string"
        return {
            "type": "array",
            "items": _to_json_schema(item_schema, path=f"{path}.item"),
            "minItems": _min_schema_list_items(path),
            "maxItems": _max_schema_list_items(path),
        }

    if isinstance(schema, bool):
        return {"type": "boolean"}

    if isinstance(schema, int) and not isinstance(schema, bool):
        if _is_float_field(path):
            return {"type": "number"}
        return {"type": "integer"}

    if isinstance(schema, float):
        return {"type": "number"}

    options = _schema_options(schema)
    if options:
        return {"type": "string", "enum": options}

    json_schema = {"type": "string"}
    if isinstance(schema, str) and schema.strip() and schema.strip().lower() != "string":
        json_schema["description"] = schema.strip()
    return json_schema


def _looks_like_json_schema(schema):
    if not isinstance(schema, dict):
        return False

    schema_keys = {
        "$schema",
        "type",
        "properties",
        "required",
        "items",
        "enum",
        "additionalProperties",
        "description",
        "minItems",
        "maxItems",
        "minimum",
        "maximum",
        "minLength",
        "maxLength",
        "oneOf",
        "anyOf",
        "allOf",
        "const",
        "title",
    }
    return "type" in schema and set(schema).issubset(schema_keys)


def _schema_argument_prompt(spec, argument_schema, json_schema):
    return textwrap.dedent(
        f"""
        Build the complete argument object for tool {spec.name}.
        Tool signature: {spec.signature}.

        Declarative argument schema:
        {json.dumps(_json_safe(argument_schema), ensure_ascii=True)}

        JSON Schema enforced by Guidance:
        {json.dumps(_json_safe(json_schema), ensure_ascii=True)}

        Generate one object that can be passed directly as Python keyword
        arguments to the tool. Never serialize nested objects or lists as
        strings. Replace every descriptive placeholder with concrete
        task-specific content. Do not output markdown, labels, hidden
        reasoning, ellipses, TODO, or TBD.
        """
    ).strip()


def _schema_var_name(step_index, path):
    suffix = re.sub(r"[^a-zA-Z0-9_]+", "_", path).strip("_").lower()
    return f"noema_env_arg_{step_index}_{suffix}"


def _schema_options(schema):
    if not isinstance(schema, str) or "|" not in schema:
        return []
    options = [option.strip() for option in schema.split("|")]
    return [option for option in options if option]


def _is_float_field(path):
    field_name = path.rsplit(".", 1)[-1].lower()
    return field_name in {
        "score",
        "confidence",
        "selection_confidence",
        "correctness",
        "relevance",
        "completeness",
        "clarity",
        "consistency",
        "grounding",
        "verification",
    }


def _max_schema_list_items(path):
    field_name = path.rsplit(".", 1)[-1].lower()
    if field_name in {"ranking", "verified_claims"}:
        return 4
    return 3


def _min_schema_list_items(path):
    field_name = path.rsplit(".", 1)[-1].lower()
    if field_name in {"ranking"}:
        return 1
    return 0


def _annotation_text(annotation):
    return _annotation_source(annotation).lower()


def _annotation_source(annotation):
    if annotation is inspect.Signature.empty:
        return ""
    return str(annotation).strip().strip("'\"")


def _is_any_annotation(annotation):
    return annotation is Any or _annotation_text(annotation) in {"any", "typing.any"}


def _is_str_annotation(annotation):
    return annotation is str or _annotation_text(annotation) == "str"


def _is_bool_annotation(annotation):
    return annotation is bool or _annotation_text(annotation) == "bool"


def _is_int_annotation(annotation):
    return annotation is int or _annotation_text(annotation) == "int"


def _is_float_annotation(annotation):
    return annotation is float or _annotation_text(annotation) == "float"


def _is_list_annotation(annotation):
    origin = get_origin(annotation)
    if origin is list:
        return True
    text = _annotation_text(annotation)
    return annotation is list or text == "list" or text.startswith("list[") or text.startswith("typing.list")


def _normalize_tool_arguments(spec, args):
    dict_parameter = _single_dict_parameter(spec)
    if dict_parameter is not None and dict_parameter not in args:
        return {dict_parameter: args}
    return args


def _single_dict_parameter(spec):
    if len(spec.parameters) != 1:
        return None
    parameter = spec.parameters[0]
    annotation = spec.parameter_annotations.get(parameter)
    if _is_dict_annotation(annotation):
        return parameter
    return None


def _is_dict_annotation(annotation):
    origin = get_origin(annotation)
    if origin is dict:
        return True
    if annotation is dict:
        return True
    if annotation is inspect.Signature.empty:
        return False
    text = _annotation_text(annotation)
    return text == "dict" or text.startswith("dict[") or text.startswith("typing.dict")


def _coerce_tool_arguments(spec, args):
    coerced = {}
    for key, value in args.items():
        annotation = spec.parameter_annotations.get(key, inspect.Signature.empty)
        try:
            coerced[key] = _coerce_tool_argument_value(value, annotation)
        except (TypeError, ValueError) as error:
            raise TypeError(f"invalid value for argument {key!r}: {error}") from error
    return coerced


def _coerce_tool_argument_value(value, annotation):
    if annotation is inspect.Signature.empty:
        return value
    if _is_str_annotation(annotation):
        return str(value)
    if _is_bool_annotation(annotation):
        if isinstance(value, bool):
            return value
        if isinstance(value, str) and value.strip().lower() in {"true", "false"}:
            return value.strip().lower() == "true"
        raise TypeError(f"expected bool, got {type(value).__name__}")
    if _is_int_annotation(annotation):
        if isinstance(value, bool):
            raise TypeError("expected int, got bool")
        return int(value)
    if _is_float_annotation(annotation):
        if isinstance(value, bool):
            raise TypeError("expected float, got bool")
        return float(value)
    if _is_list_annotation(annotation):
        if not isinstance(value, list):
            raise TypeError(f"expected list, got {type(value).__name__}")
        return value
    if _is_dict_annotation(annotation):
        if not isinstance(value, dict):
            raise TypeError(f"expected dict, got {type(value).__name__}")
        return value
    return value


def _normalize_tool_result(result, schema):
    if schema is None:
        return result

    json_schema = _to_json_schema(schema, path="result")
    value = _json_payload(result)
    value = _parse_json_payload_if_needed(value, json_schema)
    _validate_json_schema_value(value, json_schema, "result")
    return value


def _json_payload(value):
    value = value_of(value)
    if is_dataclass(value) and not inspect.isclass(value):
        return asdict(value)
    if hasattr(value, "model_dump"):
        return value.model_dump()
    if hasattr(value, "dict") and callable(value.dict):
        return value.dict()
    if isinstance(value, dict):
        return {str(key): _json_payload(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_payload(item) for item in value]
    return value


def _parse_json_payload_if_needed(value, json_schema):
    expected_type = json_schema.get("type") if isinstance(json_schema, dict) else None
    if isinstance(value, str) and expected_type in {"object", "array"}:
        try:
            return json.loads(value)
        except json.JSONDecodeError as error:
            raise ValueError(f"expected JSON {expected_type}, got an unparsable string") from error
    return value


def _validate_json_schema_value(value, schema, path):
    if schema is True or schema is None:
        return
    if schema is False:
        raise ValueError(f"{path} does not match an unsatisfiable schema")
    if not isinstance(schema, dict):
        return

    if "enum" in schema and value not in schema["enum"]:
        raise ValueError(f"{path} must be one of {schema['enum']!r}, got {value!r}")

    expected_type = schema.get("type")
    if isinstance(expected_type, list):
        errors = []
        for candidate_type in expected_type:
            try:
                _validate_json_schema_value(value, {**schema, "type": candidate_type}, path)
                return
            except ValueError as error:
                errors.append(str(error))
        raise ValueError("; ".join(errors))

    if expected_type == "object":
        _validate_json_object(value, schema, path)
        return

    if expected_type == "array":
        _validate_json_array(value, schema, path)
        return

    if expected_type == "string" and not isinstance(value, str):
        raise ValueError(f"{path} must be a string, got {type(value).__name__}")
    if expected_type == "boolean" and not isinstance(value, bool):
        raise ValueError(f"{path} must be a boolean, got {type(value).__name__}")
    if expected_type == "integer" and (isinstance(value, bool) or not isinstance(value, int)):
        raise ValueError(f"{path} must be an integer, got {type(value).__name__}")
    if expected_type == "number" and (isinstance(value, bool) or not isinstance(value, (int, float))):
        raise ValueError(f"{path} must be a number, got {type(value).__name__}")


def _validate_json_object(value, schema, path):
    if not isinstance(value, dict):
        raise ValueError(f"{path} must be an object, got {type(value).__name__}")

    properties = schema.get("properties", {})
    required = schema.get("required", [])
    for key in required:
        if key not in value:
            raise ValueError(f"{path}.{key} is required")

    additional_properties = schema.get("additionalProperties", True)
    for key, item in value.items():
        if key in properties:
            _validate_json_schema_value(item, properties[key], f"{path}.{key}")
            continue
        if additional_properties is False:
            raise ValueError(f"{path}.{key} is not allowed")
        if isinstance(additional_properties, dict):
            _validate_json_schema_value(item, additional_properties, f"{path}.{key}")


def _validate_json_array(value, schema, path):
    if not isinstance(value, list):
        raise ValueError(f"{path} must be an array, got {type(value).__name__}")

    if "minItems" in schema and len(value) < int(schema["minItems"]):
        raise ValueError(f"{path} must contain at least {schema['minItems']} item(s)")
    if "maxItems" in schema and len(value) > int(schema["maxItems"]):
        raise ValueError(f"{path} must contain at most {schema['maxItems']} item(s)")

    item_schema = schema.get("items")
    if item_schema is None:
        return
    for index, item in enumerate(value):
        _validate_json_schema_value(item, item_schema, f"{path}[{index}]")


def _argument_json_shape(spec):
    return json.dumps({name: f"<{name}>" for name in spec.parameters}, ensure_ascii=True)


def _tool_argument_error(spec, args, error):
    return {
        "error": {
            "type": "invalid_tool_arguments",
            "message": str(error),
            "expected": spec.signature,
            "received": _json_safe(args),
            "hint": "Call the same tool again with every required JSON key.",
        }
    }


def _tool_argument_schema_error(spec, error):
    return {
        "error": {
            "type": "invalid_tool_argument_schema",
            "message": str(error),
            "expected": spec.signature,
            "hint": (
                "Declare a strict argument schema for this tool, or use precise "
                "primitive annotations instead of an unconstrained dict."
            ),
        }
    }


def _tool_result_error(spec, result, error):
    return {
        "error": {
            "type": "invalid_tool_result",
            "message": str(error),
            "expected": spec.signature,
            "received": _json_safe(result),
            "hint": "Fix the tool implementation so its return value matches its declared schema.",
        }
    }


def _tool_argument_json_error(spec, raw_args, error):
    return {
        "error": {
            "type": "invalid_tool_arguments",
            "message": str(error),
            "expected": spec.signature,
            "received": str(raw_args),
            "hint": (
                "Call the same tool again with a valid one-line JSON object. "
                "Use double quotes and include every required key."
            ),
        }
    }


def _json_log(value):
    return json.dumps(_json_safe(value), ensure_ascii=True)


def _parse_json_object(value):
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        try:
            parsed = ast.literal_eval(value)
        except (SyntaxError, ValueError, TypeError):
            raise ValueError(f"NoemaEnvironment expected JSON object arguments, got: {value!r}") from error
        if not isinstance(parsed, dict):
            raise ValueError(f"NoemaEnvironment expected JSON object arguments, got: {value!r}") from error
        return _literal_json_safe(parsed)
    if not isinstance(parsed, dict):
        raise ValueError(f"NoemaEnvironment expected JSON object arguments, got: {value!r}")
    return parsed


def _literal_json_safe(value):
    if value is Ellipsis:
        return "..."
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _literal_json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_literal_json_safe(item) for item in value]
    return str(value)


def _clean_final_answer(value):
    text = str(value_of(value)).strip()
    if not text:
        return ""

    text = _remove_think_sections(text).strip()
    text = _strip_answer_label(text)
    text = _drop_meta_preamble(text)
    text = _drop_meta_tail(text)
    text = _strip_trailing_meta_parenthetical(text)

    cut_markers = (
        "\n***",
        "\n*self-correction",
        "\nself-correction",
        "\nfinal response generation",
        "\nfinal response mode",
        "\nfinal answer generation",
        "\noutputting final answer",
        "\nplan:",
        "\nwait",
        "\nthe execution sequence",
        "\nthe chosen output format",
        "\n#noema_env",
    )
    lower = text.lower()
    cut_indexes = [lower.find(marker) for marker in cut_markers if lower.find(marker) >= 0]
    if cut_indexes:
        text = text[:min(cut_indexes)]

    return text.strip()


def _drop_meta_tail(text):
    lines = text.splitlines()
    kept = []
    for line in lines:
        if _is_meta_preamble(line):
            break
        kept.append(line)
    return "\n".join(kept).strip()


def _strip_trailing_meta_parenthetical(text):
    return re.sub(
        r"\s+\((?:synthesis|summary|response|answer|classification|based on)[^)]*\)\s*$",
        "",
        text.strip(),
        flags=re.IGNORECASE,
    )


def _drop_meta_preamble(text):
    paragraphs = [paragraph.strip() for paragraph in text.split("\n\n")]
    dropped = False
    while len(paragraphs) > 1 and _is_meta_preamble(paragraphs[0]):
        paragraphs.pop(0)
        dropped = True
    if len(paragraphs) != 1:
        return "\n\n".join(paragraph for paragraph in paragraphs if paragraph)
    if _is_meta_preamble(paragraphs[0]):
        return ""
    if dropped:
        return paragraphs[0]
    return text


def _is_meta_preamble(text):
    normalized = " ".join(text.strip().lower().split())
    if not normalized:
        return False
    prefixes = (
        "final response mode",
        "final response generation",
        "final answer generation",
        "outputting final answer",
        "synthesis of actions taken",
        "self-correction",
        "refinement",
        "reasoning",
        "analysis",
        "plan:",
        "wait",
        "i need to",
        "the execution sequence",
        "the required short synthesis",
        "the request requires",
        "since all actions",
        "the synthesized response",
        "the synthesized answer",
        "the synthesis should",
        "the answer should",
        "the final answer should",
        "the task was",
    )
    if normalized.startswith(prefixes):
        return True
    return False


def _remove_think_sections(text):
    lower = text.lower()
    while "<think>" in lower and "</think>" in lower:
        start = lower.find("<think>")
        end = lower.find("</think>", start) + len("</think>")
        text = text[:start] + text[end:]
        lower = text.lower()

    lower = text.lower()
    closing_index = lower.rfind("</think>")
    if closing_index >= 0:
        text = text[closing_index + len("</think>"):]

    lower = text.lower()
    opening_index = lower.find("<think>")
    if opening_index >= 0:
        text = text[:opening_index]

    return text


def _strip_answer_label(text):
    lower = text.lower()
    candidates = []
    for marker in ("final answer:", "final answer -", "answer:", "reponse finale:"):
        if lower.startswith(marker):
            candidates.append((0, marker))
        newline_marker = f"\n{marker}"
        index = lower.rfind(newline_marker)
        if index >= 0:
            candidates.append((index + 1, marker))

    if not candidates:
        return text

    index, marker = max(candidates, key=lambda candidate: candidate[0])
    return text[index + len(marker):].strip()


def _json_safe(value):
    value = value_of(value)
    if value is None or isinstance(value, (str, int, float, bool)):
        return value
    if isinstance(value, dict):
        return {str(key): _json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple, set)):
        return [_json_safe(item) for item in value]
    return repr(value)
