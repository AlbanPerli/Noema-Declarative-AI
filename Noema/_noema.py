from guidance import gen
from Noema._AtomicTypes import *
from Noema._ListGenerator import ListGenerator
from Noema._Reflexion import Reflexion
from Noema._patternBuilder import PatternBuilder
from Noema._pyExplorer import PyExplorer
from Noema.generators import ListOf

class Noema:

    def __init__(self):
        process = []
        
    def action_needed(self, model, state):
        lm = state.llm
        lm += f"\nExtract the main action from '{model.value}'\n"
        lm += "Action: " + gen(stop=[".","\n"],name="action") + "\n"
        print("Actions: ", lm["action"])
        functions = state.memoir.retrieves(lm["action"], subject='function')
        if len(functions) > 0:
            selected_func = functions[0]
            func_name = selected_func.function_name()
            parameter_names = selected_func.parameters_names()
            print("Function name: ", func_name)
            print("Parameter names: ", parameter_names)
            
            lm += f"To do '{model.value}', you need to execute the following function: \n" + selected_func.value + "\n"
            lm += "Function call (with respect to the doc string): \n"
            lm += "res = "+func_name + "("

            parameters_values = []
            for i in range(len(parameter_names)):
                pName = parameter_names[i]
                lm += pName + "="
                stops = []
                if i == len(parameter_names) - 1:
                    stops = [")"]
                else:
                    stops = [parameter_names[i+1]+"=", ")"]
                lm += gen(stop=stops,name="p"+str(i))
                pValue = lm["p"+str(i)].strip()
                if pValue[-1] == ",":
                    pValue = pValue[:-1]
                parameters_values.append(pName+"="+pValue)
            print("Parameters values: ", parameters_values)
            print("Call will be: ", func_name + "(" + ",".join(parameters_values) + ")")
            
        state.llm += model.display_var() + "FUNCTION RES" + "\n"
        return { "value": "FUNCTION RES", "noesis": model.value, "noema": model.value }
        
    def gen_list(self, model, subject):
        atomic_type = model.type.split("[")[1].split("]")[0]
        composedType = ListGenerator(atomic_type)
        if model.annotation is not None:
            res, noema, prompt = Reflexion().execute(noesis_model=model,state=subject)
            print(f"\033[94m{model.value}\033[0m = \033[93m{res}\033[0m")
            return { "value": res, "noesis": prompt, "noema": noema}
        res = composedType.execute(noesis_model=model,state=subject)
        print(f"\033[94m{model.value}\033[0m = \033[93m{res}\033[0m")
        return { "value": res, "noesis": model.value, "noema": model.value }
    
    def gen_atomic(self, model, subject):
        instance = obj = PatternBuilder.instance().objects_by_type[model.type]()
        if model.annotation is not None:
            res, noema, prompt = Reflexion().execute(noesis_model=model,state=subject)
            print(f"\033[94m{model.value}\033[0m = \033[93m{res}\033[0m")
            return { "value": res, "noesis": prompt, "noema": noema}
        else:
            res = instance.execute(noesis_model=model,state=subject)
            print(f"\033[94m{model.value}\033[0m = \033[93m{res}\033[0m")
            return { "value": res, "noesis": model.value, "noema": model.value }
    
    def generateFromModel(self, model, subject) -> dict:
        type = model.type
        res = None
        if "list" in type:
            if model.annotation == "Action":
                print("Action needed")
                return self.action_needed(model, subject)
            else:
                return self.gen_list(model, subject)
        else:
            if model.annotation == "Action":
                print("Action needed")
                return self.action_needed(model, subject)
            else:
                return self.gen_atomic(model, subject)