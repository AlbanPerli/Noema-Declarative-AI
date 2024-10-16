import re
from .step import GenStep,Step
from .cfg import *
from guidance import models, gen, select, capture


class Select(GenStep):
    
    def __init__(self, llm_input:str, options, to:str , action=None):
        super().__init__(llm_input, to, output_type="Single Word",action=action)
        if isinstance(options, str):
            if not re.match(r'\{(\w+)\}', options):
                raise ValueError(f"La source de donnée {options} doit être une variable entre accolades.")
            self.options = re.findall(r'\{(\w+)\}', options)[0]
        elif isinstance(options, list):
            self.options = options
        elif isinstance(options, Step):
            self.options = options
        else:
            raise ValueError("The parameter must be a string (state key), a list or a Step.")
        self.display_type = "Tu réponds en sélectionnant l'option la plus pertinente."
                
    def execute(self, state):
        super().execute(state)    
        current_options = self.resolve_param(self.options, state) 
        llm = state.llm
        llm += self.display_step_name + self.current_llm_input+ " " + select(current_options, name="response")
        res = llm["response"]
        state.llm += self.display_step_name + res + "\n" 
        state.set(self.name, res)
        return res
    
    def resolve_param(self, param, state):
        if isinstance(param, str):
            return state.get(param)
        elif isinstance(param, Step):
            return param.execute(state)
        elif isinstance(param, list):
            return param
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        
    
class Word(GenStep):
    
    def __init__(self, llm_input:str, to:str , action=None):
        super().__init__(llm_input, to, output_type="Single Word",action=action)
        self.display_type = "Tu réponds avec un mot."
        
    def execute(self, state):
        super().execute(state)    
        llm = state.llm    
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.word(), name="res") + "\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        state.set(self.name, res)
        return res
    
class Sentence(GenStep):
    
    def __init__(self, llm_input:str, to:str , action=None):
        super().__init__(llm_input, to, output_type="Sentence",action=action)
        self.display_type = "Tu réponds avec une phrase."

    def execute(self, state):
        super().execute(state) 
        llm = state.llm       
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.sentence(), name="res") + ".\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        state.set(self.name, res)
        return res
    
class Int(GenStep):
    
    def __init__(self, llm_input:str, to:str , action=None):
        super().__init__(llm_input, to, output_type="Int",action=action)
        self.display_type = "Tu réponds avec un nombre."

    def execute(self, state):
        super().execute(state)    
        llm = state.llm    
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.num(), name="res") + "\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        state.set(self.name, int(res))
        return res
        
class Float(GenStep):
    
    def __init__(self, llm_input:str, to:str , action=None):
        super().__init__(llm_input, to, output_type="Float",action=action)
        self.display_type = "Tu réponds avec un nombre à virgule."

    def execute(self, state):
        super().execute(state)  
        llm = state.llm      
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.float(), name="res") + "\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        state.set(self.name, float(res))
        return res
    
class Bool(GenStep):
    
    def __init__(self, llm_input:str, to:str , action=None):
        super().__init__(llm_input, to, output_type="Bool",action=action)
        self.display_type = "Tu réponds par oui ou par non."

    def execute(self, state):
        super().execute(state)   
        llm = state.llm     
        llm += self.display_step_name + self.current_llm_input + " " + capture(G.bool(), name="res") + "\n"
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        if res == "oui":
            res = True
        else:
            res = False
        state.set(self.name, res)
        return res
    
    

class ListOf(GenStep):
    
    def __init__(self, llm_input:str, to:str , elementType:GenStep, action=None):
        super().__init__(llm_input, to, output_type="List",action=action)
        self.elementType = elementType
        
    def execute(self, state):
        super().execute(state)
        llm = state.llm
        if self.elementType is Word:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.word()), name="res") + "\n"    
        elif self.elementType is Sentence:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.sentence()), name="res") + "\n"
        elif self.elementType is Int:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.num()), name="res") + "\n"
        elif self.elementType is Float:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.float()), name="res") + "\n"
        elif self.elementType is Bool:
            llm += self.display_step_name + self.current_llm_input + " " + capture(G.arrayOf(G.bool()), name="res") + "\n"
        else:
            raise ValueError("The elementType must be a Word, Sentence, Int, Float or Bool.")
        
        res = llm["res"]
        state.llm += self.display_step_name + res + "\n"
        res = res[1:-1].split(",")
        res = [el.strip()[1:-1] for el in res]
        state.set(self.name, res)
        return res