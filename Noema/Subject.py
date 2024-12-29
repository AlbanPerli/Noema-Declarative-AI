import json
import textwrap
from guidance import models,gen,select,capture

class SingletonMeta(type):
    _instances = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            instance = super().__call__(*args, **kwargs)
            cls._instances[cls] = instance
        return cls._instances[cls]

class Subject(metaclass=SingletonMeta):
    def __init__(self, model_path:str, context_size = 512*8, verbose = False, write_graph = False):
        self.verbose = verbose
        self.model_path = model_path
        self.write_graph = write_graph
        self.llm = models.LlamaCpp(
            self.model_path,
            n_gpu_layers=99,
            n_ctx=context_size,
            echo=False,
        )
        self.structure = []
        self.stack = [self.structure]

    def enter_function(self, f_name, inst, noesis):
        func = {
            "f_name": f_name,
            "inst": inst,
            "noesis": noesis,
            "chain": []
        }
        self.stack[-1].append(func)
        self.stack.append(func["chain"])

    def append_to_chain(self, value):
        step = value
        self.stack[-1].append(step)
        if self.write_graph:
            self.to_PlantUML_diagram()
            self.to_mermaid_diagram()

    def exit_function(self, return_value):
        if len(self.stack) > 1:
            self.stack.pop()
            self.stack[-1][-1]["return"] = return_value
        else:
            raise Exception("Aucune fonction à quitter.")

    def to_PlantUML_diagram(self):
        self.generate_plantuml_sequence(self.structure)
        
    def to_mermaid_diagram(self):
        self.json_to_mermaid_sequence(self.structure)
        
    def json_to_mermaid_sequence(self, json_data):
        """
        Convertit un JSON structuré en un diagramme de séquence Mermaid.

        Args:
            json_data (list): Liste de dictionnaires représentant les fonctions et leurs chaînes.

        Returns:
            str: Chaîne contenant le code du diagramme de séquence Mermaid.
        """
        mermaid = ['sequenceDiagram']
        participants_added = set()

        def sanitize(text):
            """Échappe les caractères spéciaux pour Mermaid."""
            if type(text) == list:
                text_str = ""
                for i in range(len(text)):
                    t = str(text[i])
                    if len(t) > 50:
                        t = textwrap.fill(t, width=50)+"<br>"
                    text_str += t
                return text.replace("\n", "<br>").replace("'", "\\'").replace('"', '\\"')
            
            if type(text) != str:
                return text
            
            if len(text) > 50:
                text = textwrap.fill(text, width=50)
                            
            return text.replace("\n", "<br>").replace("'", "\\'").replace('"', '\\"')

        def process_function(function_node, caller=None):
            f_name = function_node['f_name']
            
            # Ajouter le participant si ce n'est pas déjà fait
            if f_name not in participants_added:
                mermaid.append(f"participant {f_name}")
                participants_added.add(f_name)
            
            # Ajouter une note au-dessus du participant avec 'inst'
            inst = sanitize(function_node['inst'].strip())
            mermaid.append(f"Note over {f_name}: {inst}")
            
            for element in function_node.get('chain', []):
                if 'f_name' in element:
                    sub_f_name = element['f_name']
                    
                    if sub_f_name not in participants_added:
                        mermaid.append(f"create participant {sub_f_name}")
                        participants_added.add(sub_f_name)
                    
                    sub_inst = sanitize(element['inst'].strip())
                    mermaid.append(f"Note over {sub_f_name}: {sub_inst}")
                    
                    noesis = sanitize(element['noesis'].strip())
                    mermaid.append(f"Note right of {f_name}: {noesis}")
                    
                    mermaid.append(f"{f_name} ->> {sub_f_name}: {noesis}")
                    
                    process_function(element, caller=f_name)
                    
                    ret_val = sanitize(str(element.get('return', '')))
                    mermaid.append(f"{sub_f_name} -->> {f_name}: {ret_val}")
                else:
                    noesis = sanitize(element.get('noesis', '').strip())
                    value = sanitize(str(element.get('value', '')).strip())
                    
                    mermaid.append(f"Note right of {f_name}: {noesis}")
                    
                    mermaid.append(f"{f_name} ->> {f_name}: {value}")
            
            if caller and 'return' in function_node:
                ret_val = sanitize(str(function_node['return']).strip())
                mermaid.append(f"{f_name} -->> {caller}: {ret_val}")

        for func in json_data:
            process_function(func)

        m = '\n'.join(mermaid)
        with open("diagram.mmd", "w") as f:
            f.write(m)

    
    def generate_plantuml_sequence(self, json_data, file_name="diagram.puml"):
        plantuml = ["@startuml", "!theme bluegray"]
        participants = set()
        
        def escape_note(text):
            
            if type(text) == list:
                text_str = ""
                for i in range(len(text)):
                    t = str(text[i])
                    if len(t) > 50:
                        t = textwrap.fill(t, width=50)+"\n"
                    text_str += t
                return text_str.replace('"', '\\"').replace('\n', '\\n')
            
            if type(text) != str:
                return text
            
            if len(text) > 50:
                text = textwrap.fill(text, width=50)
                            
            return text.replace('"', '\\"').replace('\n', '\\n')
        
        
        def process_function(func, parent=None):
            f_name = func.get("f_name")
            inst = func.get("inst", "").strip()
            noesis = func.get("noesis", "").strip()
            chain = func.get("chain", [])
            return_value = func.get("return")
            
            if f_name not in participants:
                plantuml.append(f"participant {f_name}")
                participants.add(f_name)
            
            if inst:
                plantuml.append(f"note over {f_name}: {escape_note(inst)}")
            
            current_actor = f_name
            
            for item in chain:
                if "f_name" in item:
                    sub_f_name = item["f_name"]
                    
                    if sub_f_name not in participants:
                        plantuml.append(f"create {sub_f_name}")
                        participants.add(sub_f_name)
                    plantuml.append(f"{current_actor} -> {sub_f_name}: Call {sub_f_name}")
                    plantuml.append("group " + sub_f_name)
                    sub_noesis = item.get("noesis", "").strip()
                    if sub_noesis:
                        plantuml.append(f"note over {sub_f_name}: {escape_note(sub_noesis)}")
                    process_function(item, parent=current_actor)
                    plantuml.append("end group")
                    
                    plantuml.append(f"{sub_f_name} --> {current_actor}: Return {escape_note(item.get('return'))}")
                    current_actor = f_name
                else:
                    value = item.get("value")
                    noesis = item.get("noesis", "").strip()
                    noema = item.get("noema", "").strip()
                    
                    if noesis:
                        plantuml.append(f"note right of {current_actor}: {escape_note(noesis)}")
                    
                    plantuml.append(f"{current_actor} -> {current_actor}: {escape_note(value)}")
        
        for func in json_data:
            process_function(func)
        
        plantuml.append("@enduml")
        plantuml_str = "\n".join(plantuml)
        with open("diagram.puml", "w") as f:
            f.write(plantuml_str)

    @classmethod
    def shared(cls):
        if cls not in SingletonMeta._instances:
            raise Exception("You must instantiate the subject with a llm path.")
        return SingletonMeta._instances[cls]
    
    def noema(self):
        return str(self.llm)