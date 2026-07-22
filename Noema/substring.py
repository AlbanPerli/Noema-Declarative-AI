from .Generator import Generator, noema_generator
from .generation import execute_substring


class Substring(Generator):
    
    hint = "Response format: extract a substring"
    
    def execute(self):
        execute_substring(self)
