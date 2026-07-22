from .Generator import Generator
from .llm import current_runtime
from guidance import gen

class Sentence(Generator):
    regex = r"[A-ZÀÂÄÉÈÊËÎÏÔŒÙÛÜÇ]?[a-zA-ZÀÂÄÉÈÊËÎÏÔŒÙÛÜÇàâäéèêëîïôœùûüç0-9\s,;:<>\{\}/=\-\+\%\*`'\"\\(\\)\-…_\$]*[.!?]$"
    hint = "Response format: a sentence"
    return_type = str
    stops = ["\n"]
    
class Paragraph(Generator):
    regex = r"[A-ZÀÂÄÉÈÊËÎÏÔŒÙÛÜÇ]?[a-zA-ZÀÂÄÉÈÊËÎÏÔŒÙÛÜÇàâäéèêëîïôœùûüç0-9\s,;:<>\{\}/=\-\+\%\*`'\"\\(\\)\-\.…\\n_\$]*[.!?]$"
    hint = "Response format: a paragraph"
    return_type = str
    stops = ["\n"]
    
class Free(Generator):
    regex = ""
    hint = "Response format: text"
    return_type = str
    
    def execute(self, max_tokens=500):
        llm = current_runtime().llm
        noesis = ""
        if self.hint != None:
            noesis = self.value + f"({self.hint})" + "\n"
        else:
            noesis = self.value + "\n"
        display_var = "#"+self.id.replace("self.", "").upper()+":"
        llm += noesis
        llm += display_var + " " + gen(name="response",max_tokens=max_tokens) + "\n"
        res = llm["response"]
        current_runtime().llm = llm
        self.noema = self.value
        self.value = res
        self.noesis = noesis
        current_runtime().append_to_chain({"value": self.value, "noema": self.noema, "noesis": self.noesis})
        if current_runtime().verbose:
            print(f"{self.id.replace('self.', '')} = \033[93m{res}\033[0m (\033[94m{self.noema + f'({self.hint})'}\033[0m)")
