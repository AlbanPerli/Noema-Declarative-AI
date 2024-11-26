import re
from typing import Annotated
from annotated_types import MinLen
from guidance import capture, gen
from pydantic import TypeAdapter
from guidance import json as jj
from Noema._AtomicGenerator import AtomicGenerator
from Noema._CustomGenerator import CustomGenerator
from Noema._patternBuilder import PatternBuilder
from Noema.cfg import *
from guidance import models, gen, select, capture, substring
from Noema._Generator import Generator
from Noema._patternBuilder import PatternBuilder
from Noema.cfg import G
    
class Email(CustomGenerator):
    grammar = G.email()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.email(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)

    
class Url(AtomicGenerator):
    grammar = G.url_http_https()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.url_http_https(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)


class Information(AtomicGenerator):
    grammar = None
    return_type = str

class Instruction(AtomicGenerator):
    grammar = None
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        state.llm += "[INST]" + noesis_model.value + "[/INST]\n"
        return "[INST]" + noesis_model.value + "[/INST]\n"


class Paragraph(AtomicGenerator):
    grammar = G.alphaNumPunctForParagraph()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += "-->"+noesis_model.value + "\n"
        if noesis_model.next_model is not None:
            llm += noesis_model.display_var() + " " + gen(name="response",stop=noesis_model.stops())
        else:
            llm += noesis_model.display_var() + " " + gen(name="response",stop=["\n"])
        res = llm["response"]
        res = res.strip()    
        res = res.replace(noesis_model.display_var(),"")        

        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)

class Fill(AtomicGenerator):
    grammar = G.alphaNumPunctForParagraph()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += "\n"+noesis_model.value[0] + "\n"
        # replacing ##Type:Name## with <blank_Type> in noesis_model.value[1] extracting the type put in the blank
        prefill = re.sub(r"##(\w+):(\w+)##", r"<blank>", noesis_model.value[1])
        llm += "#Fill-in-the-blank:\n"+prefill+"\nI will rewrite the following, replacing the <blank> values:\n " "\n"
        value = noesis_model.value[1]
        white_list_names = PatternBuilder.instance().whiteListNames()
        pattern = r"(?P<static>[^\#]+)|##(?P<type>\w+)(?::(?P<name>\w+))?##"
        matches = re.finditer(pattern, value)
        value = value.format(**local_vars)
        elements = {}
        full_response = ""
        for match in matches:
            static_part = match.group("static")
            type_name = match.group("type")
            var_name = match.group("name")

            if static_part:
                u_static_part = static_part
                llm += u_static_part
                full_response += u_static_part

            if type_name:
                if type_name in globals():
                    instance = globals()[type_name]()
                    res = None
                    if type(instance) is IntList:
                        llm += capture(G.arrayOf(G.positive_num()), name="response")
                        res = llm["response"]
                        if var_name:
                            _res = res[1:-1].split(",")
                            _res = [int(el.strip()[1:-1]) for el in _res]
                            _res = [el for el in _res if el]
                            elements[var_name] = _res
                    elif type(instance) is SentenceList:
                        ta = TypeAdapter(Annotated[list[str], MinLen(10)])
                        llm +=  jj(name="response", schema=ta)
                        res = llm["response"]
                        if var_name:
                            _res = res[1:-1].split(",")
                            _res = [str(el.strip()[1:-1]) for el in _res]
                            _res = [el for el in _res if el]
                            elements[var_name] = _res
                            
                    elif type(instance) is WordList:
                        llm += capture(G.arrayOf(G.word()), name="response")
                        res = llm["response"]
                        if var_name:
                            _res = res[1:-1].split(",")
                            _res = [str(el.strip()[1:-1]) for el in _res]
                            _res = [el for el in _res if el]
                            elements[var_name] = _res
                    elif type(instance) is BoolList:
                        llm += capture(G.arrayOf(G.bool()), name="response")
                        res = llm["response"]
                        if var_name:
                            _res = res[1:-1].split(",")
                            _res = [str(el.strip()[1:-1]).lower() == "yes" for el in _res]
                            _res = [el for el in _res if el]
                            elements[var_name] = _res
                    elif type(instance) is FloatList:
                        llm += capture(G.arrayOf(G.float()), name="response")
                        res = llm["response"]
                        if var_name:
                            _res = res[1:-1].split(",")
                            _res = [float(el.strip()[1:-1]) for el in _res]
                            _res = [el for el in _res if el]
                            elements[var_name] = _res
                    elif type(instance) is SubString:
                        llm += substring(str(state.llm), name="response")
                        res = llm["response"]
                        if var_name:
                            elements[var_name] = res
                    elif issubclass(type(instance), CustomGenerator):   
                        llm += gen(name="response", stop=instance.stops, regex=instance.regex) + "\n"
                        res = llm["response"]
                        if var_name:
                            elements[var_name] = instance.return_type(res)
                    elif issubclass(type(instance), CodeGenerator):
                        llm += "\n Produce only the code, no example or explanation." + "\n"
                        llm += f" ```{self.__class__.__name__}\n" + gen(stop="```",name="response")        
                        res = llm["response"]
                        if var_name:
                            elements[var_name] = res
                    else:
                        llm += capture(instance.grammar, name="response")  
                        res = llm["response"]
                        if var_name:
                            if type_name == "Bool":
                                elements[var_name] = res.lower() == "yes"
                            elif type_name == "Float":
                                elements[var_name] = float(res)
                            elif type_name == "Int":
                                elements[var_name] = int(res)
                            else:
                                elements[var_name] = res
                                
                    full_response += res
                else:
                    print(f"Type {type_name} not found")
        noesis_model.var_and_values = elements        
        state.llm += noesis_model.display_var() + " " + full_response + "\n"
        return full_response
    
    def extract_elements(input_string):
        pattern = r"([^{}]+)|{(\w+)}"
        matches = re.findall(pattern, input_string)

        elements = []
        for static_part, dynamic_part in matches:
            if static_part:
                elements.append(static_part.strip())
            elif dynamic_part:
                elements.append(dynamic_part)

        return elements


class Int(AtomicGenerator):
    grammar = G.num()
    return_type = int
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.num(), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)
    
class Word(AtomicGenerator):
    grammar = G.word()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
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
    
    def execute(self, noesis_model, state, local_vars = None):
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
    grammar = G.bool()
    return_type = bool
    
    def execute(self, noesis_model, state, local_vars = None):
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

    def execute(self, noesis_model, state, local_vars = None):
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
    grammar = G.alphaNumPunct()
    return_type = str

    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + " Produce only the code, no example or explanation." + "\n"
        llm += noesis_model.display_var() + f" ```{self.__class__.__name__}\n" + gen(stop="```",name="response")        
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)
    
class SentenceList(AtomicGenerator):
    grammar = G.sentence()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        ta = TypeAdapter(Annotated[list[str], MinLen(10)])
        llm += noesis_model.display_var() + " " + jj(name="response", schema=ta)
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        res = res[1:-1].split(",")
        res = [self.return_type(el.strip()[1:-1]) for el in res]
        # remove empty strings
        res = [el for el in res if el]
        return res
    
    
class BoolList(AtomicGenerator):
    grammar = G.sentence()
    return_type = bool
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.arrayOf(G.bool()), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        res = res[1:-1].split(",")
        res = [str(el.strip()[1:-1]).lower() == 'yes' for el in res]
        return res
    
class FloatList(AtomicGenerator):
    grammar = G.sentence()
    return_type = float
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.arrayOf(G.float()), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        res = res[1:-1].split(",")
        res = [self.return_type(el.strip()[1:-1]) for el in res]
        return res
    
class WordList(AtomicGenerator):
    grammar = G.sentence()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.arrayOf(G.word()), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        res = res[1:-1].split(",")
        res = [self.return_type(el.strip()[1:-1]) for el in res]
        res = [el for el in res if el]
        return res
    
class IntList(AtomicGenerator):
    grammar = G.sentence()
    return_type = int
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + capture(G.arrayOf(G.num()), name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        res = res[1:-1].split(",")
        res = [self.return_type(el.strip()[1:-1]) for el in res]
        return self.return_type(res)


class Reflexion(Generator):
    
    def __init__(self, ):
        pass
    
    def execute(self, noesis_model, state, local_vars = None):
        noema = ""
        prompt = f"""[INST]{noesis_model.value}\n Follow these steps of reasoning, using a loop to determine whether the process should continue or if the reflection is complete:
1. Initial Hypothesis: Provide a first answer or explanation based on your current knowledge.
2. Critical Analysis: Evaluate the initial hypothesis. Look for contradictions, weaknesses, or areas of uncertainty.
3. Conceptual Revision: Revise or improve the hypothesis based on the critiques from the Critical Analysis.
4. Extended Synthesis: Develop a more complete and nuanced response by incorporating additional perspectives or knowledge.
5. Loop or Conclusion: Return to the Decision Point. If the answer is now coherent and well-justified, you repond 'satisfying' and move to the Conclusion. If further refinement is needed, respond 'loop again' and go to the Critical Analysis. 
6. Final Conclusion: Once the reflection is considered complete, provide a final answer, clearly explaining why this response is coherent and well-justified, summarizing the key steps of the reasoning process.
7. Quality of the reflection: Provide a quality assessment of the reflection process. 
Done.
[/INST]

"""
        lm_copy = str(state.llm)
        lm = state.llm
        lm += prompt + "1. Initial Hypothesis: " + gen(name="reflexion",stop=["2. Critical Analysis:"]) 
        noema += "\n        ***Initial Hypothesis: " + lm["reflexion"].strip()
        counter = 2
        loop_count = 0
        while True:
                lm += f"{counter}. Critical Analysis:" 
                counter += 1
                lm += gen(name="critic",stop=[f"{counter}. Conceptual Revision:"]) 
                noema += "\n"+lm["critic"].strip()
                lm += f"{counter}. Conceptual Revision: " 
                counter += 1
                lm += gen(name="conceptual",stop=[f"{counter}. Extended Synthesis:"]) 
                noema += "\n" + lm["conceptual"].strip()
                lm += f"{counter}. Extended Synthesis: " 
                counter += 1
                lm += gen(name="synthesis",stop=[f"{counter}. Loop or Conclusion:"]) 
                noema += "\n" + lm["synthesis"].strip()
                lm += f"{counter}. Loop or Conclusion: " 
                counter += 1
                lm += capture(select(['satisfying', 'loop again']),name="finished")+ "\n"
                noema += "\n" + lm["finished"].strip()
                if lm["finished"] == "satisfying":
                    lm += f"{counter}. Final Conclusion: " 
                    counter += 1
                    lm += gen(name="response",stop=[f"{counter}. Quality of the reflection:"])
                    noema += "\n" + lm["response"].strip()
                    break
                loop_count += 1
                if loop_count >= 1:
                    lm += f"{counter}. Final Conclusion: " 
                    counter += 1
                    lm += gen(name="response",stop=[f"{counter}. Quality of the reflection:"])
                    noema += "\n" + lm["response"].strip()
                    break
                
        noema += "\nReflexion loop completed."
        res = lm["response"]
        state.llm.reset()
        state.llm += lm_copy+"\n"
        state.llm += noesis_model.display_var() + res + "\n"
        return res,noema, prompt



class Select(AtomicGenerator):
    grammar = G.sentence()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        # si noesis_model.value n'est pas de type list
        if type(noesis_model.value) is not list:
            raise Exception("Select value must be a list")
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + select(noesis_model.value, name="response")
        res = llm["response"]
        state.llm += noesis_model.display_var() + " " + res + "\n"
        return self.return_type(res)

class SubString(AtomicGenerator):
    grammar = G.sentence()
    return_type = str
    
    def execute(self, noesis_model, state, local_vars = None):
        llm = state.llm
        llm += noesis_model.value + "\n"
        llm += noesis_model.display_var() + " " + substring(state.llm, name="response")
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

class APL(CodeGenerator):
    pass

class Action:
    pass