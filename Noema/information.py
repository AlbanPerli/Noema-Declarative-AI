from .Generator import Generator
from .generation import execute_information

class Information(Generator):
    
    def execute(self):
        execute_information(self)
        
