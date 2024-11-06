from guidance import capture, gen
from Noema._AtomicGenerator import AtomicGenerator
from Noema.cfg import *

class Information(AtomicGenerator):
    grammar = None
    return_type = str


class Paragraph(AtomicGenerator):
    grammar = G.alphaNumPunct()
    return_type = str
    
    def execute(self, noesis_model, state):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.alphaNumPunct, name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)


class Int(AtomicGenerator):
    grammar = G.num()
    return_type = int
    
    def execute(self, noesis_model, state):
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.num(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)
    
class Word(AtomicGenerator):
    grammar = G.word
    return_type = str
    
    def execute(self, noesis_model, state):
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.word(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)
    
class Sentence(AtomicGenerator):
    grammar = G.sentence()
    return_type = str
    
    def execute(self, noesis_model, state):
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.sentence(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)
    
class Bool(AtomicGenerator):
    grammar = G.bool
    return_type = bool
    
    def execute(self, noesis_model, state):
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.bool(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)
    
class Float(AtomicGenerator):
    grammar = G.float
    return_type = float

    def execute(self, noesis_model, state):
        if self.grammar is None:
            state.llm += noesis_model.display_var() + noesis_model.value + "\n"
            return self.return_type(noesis_model.value)
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.float(), name="response")        
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)    

class CodeGenerator(AtomicGenerator):
    grammar = G.alphaNumPunct
    return_type = str

    def execute(self, noesis_model, state):
        print(f"CodeGenerator in {self.__class__.__name__}")
        llm = state.llm
        llm += noesis_model.value + " Produce only the code, no example or explanation." + "\n"
        llm += noesis_model.display_var() + f" ```{self.__class__.__name__}\n" + gen(stop="```",name="response")        
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)
    

class Python(CodeGenerator):
    pass

class Java(CodeGenerator):
    pass

class C(CodeGenerator):
    pass

class Cpp(CodeGenerator):
    pass

class CSharp(CodeGenerator):
    pass

class JavaScript(CodeGenerator):
    pass

class TypeScript(CodeGenerator):
    pass

class HTML(CodeGenerator):
    pass

class CSS(CodeGenerator):
    pass

class SQL(CodeGenerator):
    pass

class NoSQL(CodeGenerator):
    pass

class GraphQL(CodeGenerator):
    pass

class Rust(CodeGenerator):
    pass

class Go(CodeGenerator):
    pass

class Ruby(CodeGenerator):
    pass

class PHP(CodeGenerator):
    pass

class Shell(CodeGenerator):
    pass

class Bash(CodeGenerator):
    pass

class PowerShell(CodeGenerator):
    pass

class Perl(CodeGenerator):
    pass

class Lua(CodeGenerator):
    pass

class R(CodeGenerator):
    pass

class Scala(CodeGenerator):
    pass

class Kotlin(CodeGenerator):
    pass

class Dart(CodeGenerator):
    pass

class Swift(CodeGenerator):
    pass

class ObjectiveC(CodeGenerator):
    pass

class Assembly(CodeGenerator):
    pass

class VHDL(CodeGenerator):
    pass

class Verilog(CodeGenerator):
    pass

class SystemVerilog(CodeGenerator):
    pass

class Julia(CodeGenerator):
    pass

class MATLAB(CodeGenerator):
    pass

class COBOL(CodeGenerator):
    pass

class Fortran(CodeGenerator):
    pass

class Ada(CodeGenerator):
    pass

class Pascal(CodeGenerator):
    pass

class Lisp(CodeGenerator):
    pass

class Prolog(CodeGenerator):
    pass

class Smalltalk(CodeGenerator):
    pass


class Reflexion:
    pass

class Action:
    pass