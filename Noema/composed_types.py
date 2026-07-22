import re
from .BaseGenerator import BaseGenerator
from .Generator import noema_generator
from .llm import current_runtime
from guidance import gen
from .generation import (
    append_generation,
    coerce_value,
    display_var,
    format_noesis,
    generation_kwargs,
    generator_var,
    log_generation,
)

@noema_generator
class ListOf(BaseGenerator):
    regex = None
    return_type = list
    hint = "Response format: a list of #ITEM_TYPE# separated by carriage returns."
    stops = []
    
    def __init__(self, type=None, value=None, idx:int = None, var: str = None):
        super().__init__()
        self.type = type
        self.var = var
        self.value = value
        self.idx = idx
        
    def execute(self, max_items=None, item_max_tokens=48):
        runtime = current_runtime()
        llm = runtime.llm
        item_type = self.type or str
        local_hint = self._local_hint(item_type)
        noesis = format_noesis(self.value, local_hint)
        var = generator_var(self)
        llm += noesis 

        item_count = max_items or self._infer_count(self.value) or 4
        llm += runtime.reasoning_prelude()
        res = []
        llm += display_var(self) + "\n"
        for i in range(item_count):
            response_name = f"{var.lower()}_{i}_response"
            try:
                llm += f"{i + 1}. " + gen(
                    name=response_name,
                    **self._item_generation_kwargs(
                        runtime,
                        item_type,
                        item_max_tokens,
                        stop_text_name=f"{response_name}_stop_text",
                    ),
                ) + "\n"
            except Exception:
                if res:
                    break
                raise
            value = llm[response_name].strip()
            parsed = self._parse_lines(value)
            if not parsed:
                break
            item = parsed[0]
            stop_text_name = f"{response_name}_stop_text"
            if self._save_stop_text(item_type):
                try:
                    item += str(llm[stop_text_name])
                except KeyError:
                    pass
            res.append(self._coerce_item(item, item_type))

        runtime.llm = llm
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        append_generation(runtime, self)
        log_generation(runtime, self, res, hint=local_hint)

    @staticmethod
    def _parse_lines(response):
        lines = []
        for line in response.splitlines():
            line = line.strip()
            if not line:
                continue
            line = re.sub(r"^[-*]\s+", "", line)
            line = re.sub(r"^\d+[\.)]\s+", "", line)
            if line:
                lines.append(line)
        return lines

    @staticmethod
    def _infer_count(instruction):
        match = re.search(r"\b(\d{1,2})\b", instruction or "")
        if match:
            return int(match.group(1))
        return None

    def _local_hint(self, item_type):
        type_name = getattr(item_type, "__name__", str(item_type))
        if self.hint is None:
            return None
        return self.hint.replace("#ITEM_TYPE#", type_name)

    @staticmethod
    def _item_generation_kwargs(runtime, item_type, item_max_tokens, stop_text_name):
        regex = getattr(item_type, "regex", None)
        stop_regex = getattr(item_type, "stop_regex", None)
        stops = getattr(item_type, "stops", None)
        if not stops and not stop_regex:
            stops = ["\n"]
        save_stop_text = ListOf._save_stop_text(item_type)
        kwargs = generation_kwargs(
            runtime,
            max_tokens=getattr(item_type, "max_tokens", item_max_tokens) or item_max_tokens,
            regex=regex,
            stop_regex=stop_regex,
            stops=stops,
            save_stop_text=save_stop_text,
            save_stop_text_name=stop_text_name,
        )
        if "stop" not in kwargs and not stop_regex:
            kwargs["stop"] = "\n"
        return kwargs

    @staticmethod
    def _save_stop_text(item_type):
        return bool(getattr(item_type, "save_stop_text", False))

    @staticmethod
    def _coerce_item(value, item_type):
        return_type = getattr(item_type, "return_type", None)
        if return_type is None and item_type in {str, int, float, bool}:
            return_type = item_type
        return coerce_value(value, return_type)
