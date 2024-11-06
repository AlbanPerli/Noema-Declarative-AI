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
        names = [name.replace("[", "\[").replace("]", "\]") for name in names]
        type_white_list = "|".join(names)
        return r"([a-zA-Z_][a-zA-Z0-9_]*)\s*:\s*({})\s*=\s*(f?)('|\")(.*?)\4\s*(?:@(\w+))?".format(type_white_list)
