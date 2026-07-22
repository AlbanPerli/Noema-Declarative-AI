import inspect
from functools import wraps
import ast
import os
import re
import textwrap
from .llm import LLM, current_runtime
from .information import *
from .selectors import *
from .text_gen import *
from .atomic_types import *
from .substring import *
from .composed_types import *
from .semPy import *
from .programming_langugages import *


class ClassInstanceFinder(ast.NodeVisitor):
    def __init__(self, classes):
        self.classes = classes
        self.instances = []

    def visit_Assign(self, node):
        if isinstance(node.value, ast.Call):
            class_name = self.get_class_name(node.value.func)
            if class_name in self.classes:
                var_names = [self.get_name(t) for t in node.targets]
                args = self.get_call_args(node.value)
                self.instances.append({'variables': var_names, 
                                       'class': class_name, 
                                       'args': args})
        self.generic_visit(node)
    
    def get_class_name(self, func):
        if isinstance(func, ast.Name):
            return func.id
        elif isinstance(func, ast.Attribute):
            return func.attr
        return None

    def get_name(self, target):
        if isinstance(target, ast.Name):
            return target.id
        elif isinstance(target, ast.Attribute):
            return self.get_attribute_name(target)
        else:
            return None

    def get_attribute_name(self, attr):
        if isinstance(attr.value, ast.Name):
            return f"{attr.value.id}.{attr.attr}"
        elif isinstance(attr.value, ast.Attribute):
            return f"{self.get_attribute_name(attr.value)}.{attr.attr}"
        else:
            return attr.attr

    def get_call_args(self, call_node):
        args = [ast.literal_eval(arg) if isinstance(arg, ast.Constant) else ast.unparse(arg)
                for arg in call_node.args]
        kwargs = {kw.arg: ast.literal_eval(kw.value) if isinstance(kw.value, ast.Constant) else ast.unparse(kw.value)
                  for kw in call_node.keywords}
        return {'args': args, 'kwargs': kwargs}

class NoesisBuilder:
    
    def __init__(self,doc_string, instances):
        self.doc_string = doc_string
        self.instances = instances
        
    def build(self):
        noesis = textwrap.dedent(
            f"""
            NOEMA INSTRUCTIONS:
            {self.doc_string.strip()}

            Produce each requested field directly. Do not repeat prior wording.
            """
        ).strip()
        
        for instance in self.instances:
            class_name = instance["class"] 
            instance_class = globals()[class_name]
            hint = ""
            if instance_class.hint != None:
                hint = instance_class.hint
            if len(instance['variables']) > 1:
                raise ValueError("Multiple variables not supported")
            if len(instance['variables']) == 1:
                if len(instance['args']['args']) > 0:
                    step_name = instance['variables'][0].replace("self.", "").upper()
                    noesis += "\n#"+step_name + " : " 
                    if class_name == "ListOf":
                        value = instance['args']['args'][1]
                        value = re.sub(r"\{.*?\}", "<instruction here>", value)
                        noesis += value + " (" + hint.replace("#ITEM_TYPE#",instance['args']['args'][0]+"s") + ")"
                    else:
                        value = instance['args']['args'][0]
                        value = re.sub(r"\{.*?\}", "<instruction here>", value)
                        noesis += value
                        if instance_class.hint != None:
                            noesis += " (" + hint + ")"

        return noesis + "\n\n"

def _activate_llm(llm):
    if isinstance(llm, LLM):
        return llm.activate()

    return LLM(llm).activate()


def _decorate_noema(func, llm=None):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if llm is not None:
            _activate_llm(llm)
        
        def find_subclasses(base_class, namespace):
            subclasses = []
            for name, obj in namespace.items():
                if isinstance(obj, type) and issubclass(obj, base_class) and obj is not base_class:
                    subclasses.append((name, obj))
            return subclasses
    
        func_name = func.__name__
        doc = func.__doc__
        if doc is None:
            raise ValueError("Noema function must have a docstring")
        source_code = inspect.getsource(func)
        source_code = textwrap.dedent(source_code)
        # TODO: Add dynamic class loading
        classes_to_find = [
            'Generator', 'Information', 'Sentence', 'Paragraph', 'Free',
            'Word', 'Int', 'Float', 'Bool', 'Date', 'DateTime', 'Time',
            'Phone', 'Email', 'Select', 'SelectOrNone', 'Substring',
            'ListOf', 'SemPy',
            'Python', 'Swift', 'Java', 'C', 'Cpp', 'CSharp',
            'JavaScript', 'TypeScript', 'Ruby', 'PHP', 'Go', 'Rust',
            'Kotlin', 'Dart', 'Scala', 'R', 'MATLAB', 'Julia', 'Lua',
            'Perl', 'Shell', 'PowerShell', 'Bash', 'COBOL', 'Fortran',
            'Assembly', 'Verilog', 'VHDL',
        ]
        tree = ast.parse(source_code)
        finder = ClassInstanceFinder(classes_to_find)
        finder.visit(tree)
        noesis = NoesisBuilder(doc, finder.instances).build()
        subject = current_runtime()
        subject.llm += "\n"+noesis
        subject.enter_function(func_name, doc, noesis)
        result = None  # Initialisation de 'result'
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            subject.exit_function(result)
            raise e  # Relancer l'exception après le nettoyage
        else:
            subject.exit_function(result)
        return result
    
    return wrapper


def Noema(func=None, **subject_kwargs):
    model_path = subject_kwargs.pop("model_path", None)

    if callable(func) and model_path is None:
        return _decorate_noema(func)

    if func is None or isinstance(func, (LLM, str, os.PathLike)):
        if func is not None:
            llm = func
        elif model_path is not None:
            llm = LLM(model_path, **subject_kwargs)
        elif not subject_kwargs:
            llm = None
        else:
            raise TypeError("Noema model options require an LLM or model path.")

        if not isinstance(llm, LLM) and subject_kwargs:
            llm = LLM(llm, **subject_kwargs)

        def decorator(decorated_func):
            return _decorate_noema(decorated_func, llm)

        return decorator

    raise TypeError("Noema expects a function, an LLM, or a model path.")
    
