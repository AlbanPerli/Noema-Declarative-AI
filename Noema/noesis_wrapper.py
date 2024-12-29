import inspect
from functools import wraps
import ast
import textwrap
from .Subject import *
from .information import *
from .selectors import *
from .text_gen import *
from .atomic_types import *
from .substring import *
from .composed_types import *
from .semPy import *


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
        noesis = f"[INST]{self.doc_string}\n"
        
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
                        noesis += instance['args']['args'][1] + " (" + hint.replace("#ITEM_TYPE#",instance['args']['args'][0]+"s") + ")"
                    else:
                        noesis += instance['args']['args'][0]
                        if instance_class.hint != None:
                            noesis += " (" + hint + ")"

        return noesis+ "\n[/INST]\n\n"

def Noema(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        
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
        classes_to_find = ['Generator', 'Sentence', 'Email', 'Paragraph', 
                           'Name', 'Address', 'Phone', 'Date', 'Time', 
                           'Number', 'Select', 'SelectOrNone', 'Substring', 
                           'Information', 'Free', 'ListOf', 'SemPy']
        tree = ast.parse(source_code)
        finder = ClassInstanceFinder(classes_to_find)
        finder.visit(tree)
        noesis = NoesisBuilder(doc, finder.instances).build()
        Subject().shared().llm += "\n"+noesis
        Subject().shared().enter_function(func_name, doc, noesis)
        result = None  # Initialisation de 'result'
        try:
            result = func(*args, **kwargs)
        except Exception as e:
            Subject().shared().exit_function(result)
            raise e  # Relancer l'exception après le nettoyage
        else:
            Subject().shared().exit_function(result)
        return result
    
    return wrapper

    
