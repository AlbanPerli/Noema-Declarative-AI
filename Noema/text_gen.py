from .Generator import Generator
from .generation import execute_generation

class Sentence(Generator):
    regex = None
    hint = "Response format: one sentence. Stop after the final punctuation"
    return_type = str
    stop_regex = r"[.!?]"
    save_stop_text = True
    max_tokens = 36
    
class Paragraph(Generator):
    regex = None
    hint = "Response format: one concise final sentence. Do not repeat phrases"
    return_type = str
    stop_regex = r"[.!?]"
    save_stop_text = True
    max_tokens = 80
    
class Free(Generator):
    regex = ""
    hint = "Response format: text"
    return_type = str
    max_tokens = 500
    
    def execute(self, max_tokens=None):
        execute_generation(self, max_tokens=max_tokens or self.max_tokens)
