from guidance import models,gen,select,capture

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Subject(metaclass=SingletonMeta):
    def __init__(self, model_path:str, context_size = 512*8, verbose = False):
        self.verbose = verbose
        self.model_path = model_path
        self.llm = models.LlamaCpp(
            self.model_path,
            n_gpu_layers=99,
            n_ctx=context_size,
            echo=False,
        )

    @classmethod
    def shared(cls):
        if cls not in SingletonMeta._instances:
            raise Exception("You must instantiate the subject with a llm path.")
        return SingletonMeta._instances[cls]
    
    def noema(self):
        return str(self.llm)