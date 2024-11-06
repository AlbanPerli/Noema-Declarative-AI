
import importlib
import inspect
import re
from Noema._ListGenerator import ListGenerator

class PyExplorer:
    
    @staticmethod
    def extractTypeWhiteList(module_name):
        class_names, object_dict = PyExplorer._extract_class_names_and_objects(module_name)
        objects = []
        # get all objects from object_dict
        for key in object_dict:
            objects.append(object_dict[key])
        names, composed_object_dict = PyExplorer.build_composed_generators_names(objects)
        class_names.extend(names)
        object_dict.update(composed_object_dict)

        return class_names, object_dict
    
    @staticmethod
    def build_composed_generators_names(atomic_objects):
        composed_generators = []
        object_dict = {}
        for atomic_object in atomic_objects:
             obj = ListGenerator(atomic_object())
             obj_name = obj.to_string_name()
             composed_generators.append(obj_name)
             object_dict[obj_name] = obj
        return composed_generators, object_dict
    
    @staticmethod
    def _extract_class_names_and_objects(module_name):
        module = importlib.import_module(module_name)
        class_names = []
        object_dict = {}
        for name, obj in inspect.getmembers(module, inspect.isclass):
            if obj.__module__ == module_name:
                class_names.append(name)
                object_dict[name] = obj
        return class_names, object_dict
    
    
    @staticmethod
    def import_from_string(import_statement, namespace) -> dict :
        if import_statement.startswith("from "):
            parts = import_statement.split()
            module_name = parts[1]
            attribute_name = parts[3]
            if attribute_name == "*":
                namespace = PyExplorer.import_module_all(module_name, namespace)
            else:
                module = importlib.import_module(module_name)
                namespace[attribute_name] = getattr(module, attribute_name)
        elif import_statement.startswith("import "):
            module_name = import_statement.split()[1]
            namespace[module_name] = importlib.import_module(module_name)
        else:
            raise ValueError("Instruction d'import invalide.")
        
        return namespace
    
    @staticmethod
    def import_module_all(module_name, namespace):
        module = importlib.import_module(module_name)

        for name in dir(module):
            if not name.startswith('_'):
                namespace[name] = getattr(module, name)
                
        return namespace
    
    @staticmethod
    def create_name_space(sender) -> dict:
        namespace = {}
        namespace['self'] = sender
        calling_module = inspect.getmodule(type(sender))
        if calling_module is None:
            return namespace
        source_code = inspect.getsource(calling_module)
        imports = re.findall(r'^(import .+|from .+ import .+)', source_code, re.MULTILINE)
        for imp in imports:
            namespace = PyExplorer.import_from_string(imp, namespace)
        return namespace