import re
from .BaseGenerator import BaseGenerator
from .Generator import noema_generator
from .Subject import Subject
from guidance import gen

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
        llm = Subject().shared().llm
        noesis = ""
        local_hint = ""
        if self.hint != None:
            local_hint = self.hint.replace("#ITEM_TYPE#", self.type.__name__)
            noesis = self.value + f"({local_hint})" + "\n"
        else:
            noesis = self.value + "\n"
        var = "" 
        display_var = ""
        if self.idx != None:
            var = self.id.replace("self.", "").upper()+f"_{self.idx}"
        else:
            var = self.id.replace("self.", "").upper()
        display_var = "#"+f"{var}:"
        llm += noesis 

        item_count = max_items or self._infer_count(self.value) or 4
        res = []
        llm += display_var + "\n"
        for i in range(item_count):
            response_name = f"{var.lower()}_{i}_response"
            try:
                llm += f"{i + 1}. " + gen(
                    name=response_name,
                    max_tokens=item_max_tokens,
                    stop="\n",
                ) + "\n"
            except Exception:
                if res:
                    break
                raise
            value = llm[response_name].strip()
            parsed = self._parse_lines(value)
            if not parsed:
                break
            res.append(parsed[0])

        Subject.shared().llm = llm
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        Subject().shared().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if Subject().shared().verbose:
            print(f"{var} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({local_hint})'}\033[0m)")    

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
