from guidance import models

from Noema._noema import Noema
from .memoir import Memoir

class Subject:
    def __init__(self, llm_path):
        self.data = {}
        self.namespace_stack = []
        self.llm = models.LlamaCpp(
            llm_path,
            n_gpu_layers=99,
            n_ctx=512*8,
            echo=False
        )
        self.noesis = ""
        self.noema = Noema()
        self.memoir = Memoir()
            
    def add_knowledge(self, knowledge):
        self.memoir.add(knowledge, "knowledge")
            
    def add_capabilities(self, module_name):
        self.memoir.load_functions_from_module(module_name)


    def __str__(self):
        return str(self.data)