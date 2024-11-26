from guidance import gen
from Noema._AtomicTypes import *
from Noema._patternBuilder import PatternBuilder
from Noema._pyExplorer import PyExplorer


class Noema:

    def __init__(self):
        process = []
        
    def action_needed(self, model, state, local_vars, verbose):
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
        return { "value": "FUNCTION RES", "noesis": model.value, "noema": model.value, "variables":{} }
    
    def gen_atomic(self, model, subject, local_vars, verbose):
        instance = obj = PatternBuilder.instance().objects_by_type[model.type]()
        if model.type == "Fill":
            res = instance.execute(noesis_model=model,state=subject,local_vars=local_vars)
            if verbose:
                print(f"{model.variable} = \033[93m{res}\033[0m (\033[94m{model.value[0]}\033[0m)")
            return { "value": res, "noesis": model.value, "noema": model.value, "variables":{}}
        elif model.type == "Reflexion":
            res, noema, prompt = Reflexion().execute(noesis_model=model,state=subject)
            if verbose:
                print(f"{model.variable} = \033[93m{res}\033[0m (\033[94m{prompt}\033[0m)")
            return { "value": res, "noesis": model.value, "noema": noema, "variables":{}}
        elif model.type == "Information":
            res = instance.execute(noesis_model=model,state=subject)
            if verbose:
                print(f"{model.variable} = \033[93m{res}\033[0m (\033[94mINFORMATION\033[0m)")
            return { "value": res, "noesis": model.value, "noema": model.value, "variables":{} }
        else:
            res = instance.execute(noesis_model=model,state=subject)
            if verbose:
                print(f"{model.variable} = \033[93m{res}\033[0m (\033[94m{model.value}\033[0m)")
            return { "value": res, "noesis": model.value, "noema": model.value, "variables":{}} 

    def generateFromModel(self, model, subject, local_vars, verbose) -> dict:
        type = model.type
        res = None
        if model.annotation == "Action":
            return self.action_needed(model, subject, local_vars, verbose)
        else:
            return self.gen_atomic(model, subject, local_vars, verbose)