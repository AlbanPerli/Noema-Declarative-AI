import re
from Noema._pyExplorer import PyExplorer

class PatternBuilder:
    
    _instance = None  # Variable de classe pour stocker l'instance unique
    _initialized = False  # Indicateur pour contrôler l'initialisation
    def __new__(cls, *args, **kwargs):
        if cls._instance is None:
            cls._instance = super(PatternBuilder, cls).__new__(cls)
        return cls._instance

    def __init__(self, value=None):
        if not self.__class__._initialized:
            self.objects_by_type = {}
            self.noesis_pattern =  self.build_noesis_pattern()
            self.type_white_list = None
            self.type_white_list_names = None
            self.__class__._initialized = True  

    @classmethod
    def instance(cls, value=None):
        if cls._instance is None:
            cls._instance = cls(value)
        return cls._instance
        
    def build_noesis_pattern(self):
        atomicTypesModuleName = "Noema._AtomicTypes"
        names,obj_dict = PyExplorer.extractTypeWhiteList(atomicTypesModuleName)
        self.objects_by_type = obj_dict
        self.type_white_list_names = [name.replace("[", "\[").replace("]", "\]") for name in names]
        self.type_white_list = "|".join(self.type_white_list_names)
        return r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*({})\s*=\s*(f?)\s*\(*\s*((?:'''|\"\"\"|'|\"))\s*(.*?)\s*\4\s*\)*\s*(?:@(\w+)\s*(?:\(\s*(.*?)\s*\))?)?".format(self.type_white_list)

    def whiteListNames(self):
        atomicTypesModuleName = "Noema._AtomicTypes"
        names,obj_dict = PyExplorer.extractTypeWhiteList(atomicTypesModuleName)
        self.type_white_list_names = [name.replace("[", "\[").replace("]", "\]") for name in names]
        return self.type_white_list_names


