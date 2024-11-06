from Noema._AtomicTypes import *
from Noema._ListGenerator import ListGenerator
from Noema._Reflexion import Reflexion
from Noema._patternBuilder import PatternBuilder
from Noema._pyExplorer import PyExplorer
from Noema.generators import ListOf

class Noema:

    def __init__(self):
        process = []
        
    def generateFromModel(self, model, subject) -> dict:
        type = model.type
        obj = PatternBuilder.instance().objects_by_type[type]
        res = None
        if "list" in type:
            atomic_type = type.split("[")[1].split("]")[0]
            composedType = ListGenerator(atomic_type)
            if model.annotation is not None:
                res, noema, prompt = Reflexion().execute(noesis_model=model,state=subject)
                print(f"\033[94m{model.value}\033[0m = \033[93m{res}\033[0m")
                return { "value": res, "noesis": prompt, "noema": noema}
            
            res = composedType.execute(noesis_model=model,state=subject)
            print(f"\033[94m{model.value}\033[0m = \033[93m{res}\033[0m")
            return { "value": res, "noesis": model.value, "noema": model.value }
        else:
            instance = obj()
            if model.annotation is not None:
                res, noema, prompt = Reflexion().execute(noesis_model=model,state=subject)
                print(f"\033[94m{model.value}\033[0m = \033[93m{res}\033[0m")
                return { "value": res, "noesis": prompt, "noema": noema}
            else:
                res = instance.execute(noesis_model=model,state=subject)
                print(f"\033[94m{model.value}\033[0m = \033[93m{res}\033[0m")
        return { "value": res, "noesis": model.value, "noema": model.value }