from __future__ import annotations

import copy
import inspect
import json
import re
import textwrap
from dataclasses import dataclass, field
from typing import Any, Callable

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
        self._noema_environment_verbose = False

        for step_index in range(max_steps):
            decision = self._decide(prompt, run, step_index, max_tokens, planner)
            if decision.is_final:
                run.answer = _clean_final_answer(decision.answer or "")
                self._log_final(step_index, run.answer)
                return run if return_run else run.answer

            observation = self.invoke(decision.tool, **decision.args)
            run.observations.append(observation)
            self._log_observation(step_index, observation)

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
        self._noema_environment_verbose = bool(getattr(runtime, "verbose", False))
        specs = self.tool_specs()
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
            args_name = f"noema_environment_args_{step_index}"
            llm += self._argument_prompt(spec)
            llm += f"\n#NOEMA_ENV_ARGS_JSON_{step_index}: "
            llm += gen(
                name=args_name,
                regex=r"\{[^\n]*\}",
                **runtime.generation_kwargs(self.argument_tokens),
            ) + "\n"
            args = _parse_json_object(llm[args_name])
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


def _format_tool_call(tool_name, args):
    if not args:
        return f"{tool_name}()"
    arguments = ", ".join(f"{name}={value!r}" for name, value in args.items())
    return f"{tool_name}({arguments})"


def _json_log(value):
    return json.dumps(_json_safe(value), ensure_ascii=True)


def _parse_json_object(value):
    try:
        parsed = json.loads(value)
    except json.JSONDecodeError as error:
        raise ValueError(f"NoemaEnvironment expected JSON object arguments, got: {value!r}") from error
    if not isinstance(parsed, dict):
        raise ValueError(f"NoemaEnvironment expected JSON object arguments, got: {value!r}")
    return parsed


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
