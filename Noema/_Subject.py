from guidance import models

from Noema._noema import Noema

class Subject:
    def __init__(self, llm_path):
        self.data = {}
        self.namespace_stack = []
        self.parents = []
        self.llm = models.LlamaCpp(
            llm_path,
            n_gpu_layers=99,
            n_ctx=512*3,
            echo=False,
        )
        self.noesis = ""
        self.noema = Noema()
            
    def __str__(self):
        return str(self.llm)