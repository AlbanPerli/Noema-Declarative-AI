from guidance import capture
from Noema._AtomicGenerator import AtomicGenerator
from Noema.cfg import *

class Information(AtomicGenerator):
    grammar = None
    return_type = str

class Int(AtomicGenerator):
    grammar = G.num()
    return_type = int
    
    def execute(self, noesis_model, state):
        print(f"Executing {self.__class__.__name__}")
        print(f"Model: {noesis_model.value}")
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.display_var() + " " + noesis_model.value + " " + capture(G.num(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        print(f"Response: {res}")
        print(f"Result: {self.return_type(res)}")
        return self.return_type(res)
    
class Word(AtomicGenerator):
    grammar = G.word
    return_type = str
    
    def execute(self, noesis_model, state):
        print(f"Executing {self.__class__.__name__}")
        print(f"Model: {noesis_model.value}")
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.display_var() + " " + noesis_model.value + " " + capture(G.word(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        print(f"Response: {res}")
        print(f"Result: {self.return_type(res)}")
        return self.return_type(res)
    
class Sentence(AtomicGenerator):
    grammar = G.sentence()
    return_type = str
    
    def execute(self, noesis_model, state):
        print(f"Executing {self.__class__.__name__}")
        print(f"Model: {noesis_model.value}")
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.display_var() + " " + noesis_model.value + " " + capture(G.sentence(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        print(f"Response: {res}")
        print(f"Result: {self.return_type(res)}")
        return self.return_type(res)
    
class Bool(AtomicGenerator):
    grammar = G.bool
    return_type = bool
    
    def execute(self, noesis_model, state):
        print(f"Executing {self.__class__.__name__}")
        print(f"Model: {noesis_model.value}")
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.display_var() + " " + noesis_model.value + " " + capture(G.bool(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        print(f"Response: {res}")
        print(f"Result: {self.return_type(res)}")
        return self.return_type(res)
    
class Float(AtomicGenerator):
    grammar = G.float
    return_type = float

    def execute(self, noesis_model, state):
        print(f"Executing {self.__class__.__name__}")
        print(f"Model: {noesis_model.value}")
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.display_var() + " " + noesis_model.value + " " + capture(G.float(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        print(f"Response: {res}")
        print(f"Result: {self.return_type(res)}")
        return self.return_type(res)

class Reflexion:
    pass

class Action:
    pass