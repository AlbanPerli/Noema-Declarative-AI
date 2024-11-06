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
        self.builder = PyNoesisBuilder()
        self.noema = Noema()
    
    def go(self, subject):
        self.subject = subject
        infos = self.builder.build_noesis(self.description,sender=self)
        self.subject.llm += infos["noesis"]
        self.ref_code_lines = infos["code_ref"]
        self.ref_model_by_line = infos["model_ref"]
        self.updated_code_lines = infos["code_updated"]
        self.updated_model_by_line = infos["model_updated"]
        return self.run()
        
    def produceValue(self, model) -> dict:
        return self.noema.generateFromModel(model,self.subject)
        
    def trace_func(self, frame, event, arg):
        if event == 'line':
            # filename = frame.f_code.co_filename
            lineno = frame.f_lineno
            try:
                if lineno in self.updated_model_by_line:
                    local_vars = frame.f_locals
                    if self.updated_model_by_line[lineno].variable in local_vars:
                        model = self.updated_model_by_line[lineno]
                        if isinstance(local_vars.get(model.variable), Generator):
                            model = self.updated_model_by_line[lineno]
                            original_value = model.original_value
                            original_value = original_value.format(**local_vars)        
                            model.value = str(original_value)
                            produced_value = self.produceValue(model)
                            local_vars[model.variable].value = produced_value["value"]
                            local_vars[model.variable].noesis = produced_value["noesis"]
                            local_vars[model.variable].noema = produced_value["noema"]
                    else:
                        print(f"Var {self.updated_model_by_line[lineno].variable} not found in local vars")
            except Exception as e:
                print(f"Error while tracing line {lineno}: {e}")
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
            return result
        except Exception as e:
            print(f"Error while executing '{method_name}': {e}")
        finally:
            sys.settrace(None)

    
