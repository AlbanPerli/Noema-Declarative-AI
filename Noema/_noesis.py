import importlib
import re
import inspect
import sys
import linecache
import os
from Noema._Generator import Generator
from Noema._noesisModel import NoesisModel
from Noema._patternBuilder import PatternBuilder
from Noema._pyExplorer import PyExplorer
from Noema._pyNoesisBuilder import PyNoesisBuilder
from Noema._noema import Noema

class Noesis:

    def __init__(self):
        self.pattern = PatternBuilder.instance().noesis_pattern
        self.ref_code_lines = []
        self.updated_code_lines = []
        self.ref_model_by_line = {}
        self.updated_model_by_line = {}
        self.marks = []
        self.builder = PyNoesisBuilder()
        self.noema = Noema()
        self.needs_var_update = True
        self.execution_flow = []
    
    def constitute(self, subject, verbose=False):
        self.verbose = verbose
        self.subject = subject
        self.previous_state = str(self.subject.llm)
        self.subject.llm.reset()
        infos = self.builder.build_noesis(self.description,sender=self)
        self.subject.parents.append(self)
        self.subject.llm += infos["noesis"]
        self.ref_code_lines = infos["code_ref"]
        self.ref_model_by_line = infos["model_ref"]
        self.updated_code_lines = infos["code_updated"]
        self.updated_model_by_line = infos["model_updated"]
        return self.run()
        
    def produceValue(self, model, local_vars) -> dict:
        return self.noema.generateFromModel(model,self.subject, local_vars=local_vars, verbose=self.verbose)
        
    def append_flow(self, lineno, model, produced_value):
        self.execution_flow.append((lineno, model, produced_value))
        
    def trace_func(self, frame, event, arg):
        if frame.f_code.co_name != "updated_description":
            return None
        if event == 'line':
            lineno = frame.f_lineno
            line = linecache.getline(frame.f_code.co_filename, lineno)
            try:
                if lineno in self.updated_model_by_line:
                    local_vars = frame.f_locals
                    if self.needs_var_update:
                        for k,model in self.updated_model_by_line.items():
                            for key, value in model.var_and_values.items():
                                local_vars[model.variable].__dict__[key] = value
                        self.needs_var_update = False
                    if self.updated_model_by_line[lineno].variable in local_vars:
                        model = self.updated_model_by_line[lineno]
                        if isinstance(local_vars.get(model.variable), Generator):
                            produced_value = None
                            original_value = model.original_value
                            if model.type == "Fill":
                                original_value = model.original_value
                                goal = original_value[0]
                                fill = original_value[1]
                                goal = goal.format(**local_vars)
                                white_list = PatternBuilder.instance().whiteListNames()
                                for type_name in white_list:
                                    fill = re.sub(
                                        r"\{" + type_name + r"(:[_a-zA-Z][_a-zA-Z0-9]*)?\}",
                                        r"##" + type_name + r"\1##",
                                        fill,
                                    )
                                    
                                fill = fill.format(**local_vars)
                                model.value = (goal,fill)
                                produced_value = self.produceValue(model,local_vars=local_vars)
                                
                                for key, value in model.var_and_values.items():
                                    local_vars[model.variable].__dict__[key] = value
                            else:
                                original_value = model.original_value
                                original_value = original_value.format(**local_vars)        
                                model.value = str(original_value)
                                produced_value = self.produceValue(model,local_vars=local_vars)
                            
                            local_vars[model.variable].value = produced_value["value"]
                            local_vars[model.variable].noesis = produced_value["noesis"]
                            local_vars[model.variable].noema = produced_value["noema"]
                        self.append_flow(lineno, model, produced_value=produced_value)
                    # else:
                    #     print(f"Var {self.updated_model_by_line[lineno].variable} not found in local vars")
            except Exception as e:
                pass
                # print(f"Error while tracing line {lineno}: {e}")
                # print("Line", line)
        return self.trace_func

    def run(self):
        def local_trace(frame, event, arg):
            return self.trace_func(frame, event, arg)        
        namespace = PyExplorer.create_name_space(self)
        updated_code = "\n".join(self.updated_code_lines)
        method_name = "updated_description"
        exec(updated_code, globals(), namespace)
        updated_description = namespace[method_name]
        setattr(self, method_name, updated_description)
        globals().update(namespace)
        try:
            sys.settrace(local_trace)
            exec(f"result = self.{method_name}(self)", globals(), namespace)
            result = namespace.get('result')
            self.subject.parents.pop()
            return result
        except Exception as e:
            print(f"Error while executing '{method_name}': {e}")
        finally:
            if len(self.subject.parents) == 1:
                self.subject.llm.reset()
                self.subject.llm += self.previous_state
                sys.settrace(None)
                
    # def build_graph(self):
    #     graph = "graph TD\n"
    #     for i, (lineno, model, produced_value) in enumerate(self.execution_flow):
    #         variable = model.variable
    #         value = produced_value['value']
    #         graph += f'    {i}["{variable} = {value}"]\n'
    #         if i > 0:
    #             prev_lineno, prev_model, prev_produced_value = self.execution_flow[i - 1]
    #             graph += f'    {i-1} --> {i}\n'
    #     return graph