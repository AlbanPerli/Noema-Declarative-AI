import json as json_module

from guidance import gen, json as guidance_json, select, substring

from .llm import current_runtime


_YELLOW = "\033[93m"
_BLUE = "\033[94m"
_RESET = "\033[0m"


class NoemaGenerationError(Exception):
    pass


def generator_var(generator):
    base = generator.id.replace("self.", "").upper()
    if getattr(generator, "idx", None) is not None:
        return f"{base}_{generator.idx}"
    return base


def display_var(generator):
    return f"#{generator_var(generator)}:"


def format_noesis(value, hint=None):
    text = "" if value is None else str(value)
    if hint is None:
        return f"{text}\n"
    return f"{text}({hint})\n"


def generation_kwargs(
    runtime,
    *,
    max_tokens=None,
    regex=None,
    stop_regex=None,
    stops=None,
    save_stop_text=False,
    save_stop_text_name="response_stop_text",
):
    kwargs = runtime.generation_kwargs(max_tokens)
    if regex:
        kwargs["regex"] = regex
    if stop_regex:
        kwargs["stop_regex"] = stop_regex
    if stops:
        kwargs["stop"] = stops
    if save_stop_text:
        kwargs["save_stop_text"] = save_stop_text_name
    return kwargs


def coerce_value(raw, return_type):
    if return_type is None:
        return raw
    if return_type is bool:
        if raw is True or str(raw).strip() == "True":
            return True
        if raw is False or str(raw).strip() == "False":
            return False
        raise NoemaGenerationError(f"Expected Boolean value, got {raw!r}.")
    try:
        return return_type(raw)
    except (TypeError, ValueError) as error:
        raise NoemaGenerationError(
            f"Could not coerce generated value {raw!r} to {return_type}."
        ) from error


def append_generation(runtime, generator):
    runtime.append_to_chain(
        {
            "value": generator.value,
            "noema": generator.noema,
            "noesis": generator.noesis,
        }
    )


def log_generation(runtime, generator, raw=None, *, hint=None):
    if not getattr(runtime, "verbose", False):
        return
    displayed = generator.value if raw is None else raw
    local_hint = generator.hint if hint is None else hint
    if local_hint is None:
        context = str(generator.noema)
    else:
        context = f"{generator.noema}({local_hint})"
    print(
        f"{generator_var(generator)} = {_YELLOW}{displayed}{_RESET} "
        f"({_BLUE}{context}{_RESET})"
    )


def execute_generation(
    generator,
    *,
    max_tokens=None,
    regex=None,
    stop_regex=None,
    stops=None,
    save_stop_text=False,
    prefix="",
    extra_prompt=None,
):
    runtime = current_runtime()
    llm = runtime.llm
    max_tokens = generator.max_tokens if max_tokens is None else max_tokens
    noesis = format_noesis(generator.value, generator.hint)

    llm += noesis
    if extra_prompt:
        llm += str(extra_prompt).rstrip() + "\n"
    llm += runtime.reasoning_prelude()
    llm += display_var(generator) + " " + prefix + gen(
        name="response",
        **generation_kwargs(
            runtime,
            max_tokens=max_tokens,
            regex=regex,
            stop_regex=stop_regex,
            stops=stops,
            save_stop_text=save_stop_text,
        ),
    ) + "\n"

    raw = llm["response"]
    if save_stop_text:
        raw += str(llm["response_stop_text"])

    runtime.llm = llm
    generator.noema = generator.value
    generator.value = coerce_value(raw, generator.return_type)
    generator.noesis = noesis
    append_generation(runtime, generator)
    log_generation(runtime, generator, raw)
    return generator


def execute_selection(generator, *, allow_none=False):
    options = list(generator.options or [])
    if allow_none and "None" not in options:
        options.append("None")
    if not options:
        raise NoemaGenerationError("Select requires at least one option.")

    runtime = current_runtime()
    llm = runtime.llm
    noesis = format_noesis(generator.value, generator.hint)
    llm += noesis
    llm += display_var(generator) + " " + select(options, name="response") + "\n"
    raw = llm["response"]
    if raw not in options:
        raise NoemaGenerationError(f"Select generated {raw!r}, expected one of {options!r}.")

    runtime.llm = llm
    generator.noema = generator.value
    generator.value = None if allow_none and raw == "None" else raw
    generator.noesis = noesis
    append_generation(runtime, generator)
    log_generation(runtime, generator, raw, hint=f"{generator.hint} : {options}")
    return generator


def execute_substring(generator):
    runtime = current_runtime()
    llm = runtime.llm
    noesis = format_noesis(generator.value, generator.hint)
    llm += noesis
    llm += display_var(generator) + " " + substring(generator.value, name="response") + "\n"
    raw = llm["response"]

    runtime.llm = llm
    generator.noema = generator.value
    generator.value = raw
    generator.noesis = noesis
    append_generation(runtime, generator)
    log_generation(runtime, generator, raw)
    return generator


def execute_information(generator):
    runtime = current_runtime()
    noesis = display_var(generator) + " " + str(generator.value) + "\n"
    runtime.llm += noesis
    generator.noema = generator.value
    generator.noesis = noesis
    append_generation(runtime, generator)
    if getattr(runtime, "verbose", False):
        hint = f"({generator.hint})" if generator.hint is not None else ""
        print(f"{generator.id.replace('self.', '')} = {_BLUE}{generator.noema}{hint}{_RESET}")
    return generator


def execute_json_object(generator, *, max_tokens=None):
    runtime = current_runtime()
    llm = runtime.llm
    max_tokens = generator.max_tokens if max_tokens is None else max_tokens
    schema_text = json_module.dumps(generator.schema, ensure_ascii=True)
    noesis = format_noesis(generator.value, f"{generator.hint}: {schema_text}")

    json_kwargs = {}
    if max_tokens is not None:
        json_kwargs["max_tokens"] = max_tokens
    temperature = getattr(runtime, "temperature", None)
    if temperature is not None:
        json_kwargs["temperature"] = temperature

    llm += noesis
    llm += runtime.reasoning_prelude()
    llm += display_var(generator) + " " + guidance_json(
        name="response",
        schema=generator.schema,
        separators=(",", ": "),
        whitespace_flexible=True,
        **json_kwargs,
    ) + "\n"

    raw = llm["response"]
    parsed = json_module.loads(str(raw))
    if not isinstance(parsed, dict):
        raise NoemaGenerationError(f"Expected JSON object, got {type(parsed).__name__}.")

    runtime.llm = llm
    generator.noema = generator.value
    generator.value = parsed
    generator.noesis = noesis
    append_generation(runtime, generator)
    log_generation(runtime, generator, json_module.dumps(parsed, ensure_ascii=True))
    return generator
