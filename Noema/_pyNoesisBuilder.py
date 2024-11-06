

import inspect
import re

from Noema._noesisModel import NoesisModel
from Noema._patternBuilder import PatternBuilder


class PyNoesisBuilder:
    
    pattern = PatternBuilder.instance().noesis_pattern
    
    def __init__(self):
        pass
        
    def build_noesis(self, description, sender=None):
        ref_code_lines = []
        ref_model_by_line = {}
        noesis = """[SYSTEM] You are functioning like an hybrid of an Assistant and a python interpreter.
For the python interpreter, instructions are provided in the form of a python program.
For the Assistant, special instruction begins with #TASK_NAME: followed by the instruction that needs to be executed.
[/SYSTEM]"""
        # noesis = ""
        source = inspect.getsource(description)        
        system_prompt = inspect.getdoc(description)
        noesis += "\n<s>[INST]"+"You are functionning in a loop of though.\n"+system_prompt+"\nHere is the code/reasonning you are currently executing:\n\n"
        source = self.clean_code(source)
        code_lines = source.splitlines()
        code_lines = [line for line in code_lines if line.strip()]
        ref_code_lines = code_lines
        context = {"self":sender}
        for i in range(len(code_lines)):
            line = code_lines[i]
            current_indent = len(line) - len(line.lstrip())
            line = line.strip()
            if re.match(self.pattern, line):
                model = self.extract_and_evaluate(line,context)
                if model.value[-1] not in ['.', '!', '?']:
                    model.value += '.'
                if model.type == "Information":
                    noesis += " "*current_indent+ f"{model.display_var()} {model.value}\n"
                else:
                    noesis += " "*current_indent+ f"{model.display_var()} {model.value}\n"# Respond with a {model.type}\n"
                ref_model_by_line[i] = model
            else:
               noesis += " "*current_indent+ f"{line}\n"
        noesis += "[/INST]\n\n"
        updated_code, updated_model = self.update_code(ref_code_lines, ref_model_by_line)
        return {"noesis":noesis, "code_ref":ref_code_lines, "model_ref":ref_model_by_line, "code_updated":updated_code, "model_updated":updated_model}
    
    
    def update_code(self, ref_code_lines, ref_model_by_line):
        updated_model_by_line = {}
        updated_code_lines = ["def updated_description(self):"]
        for key in ref_model_by_line:
            print(ref_model_by_line[key].variable)
            updated_code_lines.append(ref_model_by_line[key].variable+" = Generator()")
        instruction_nb = len(updated_code_lines)
        updated_code_lines.extend(ref_code_lines)
        for key in ref_model_by_line:
            updated_model_by_line[key+instruction_nb+1] = ref_model_by_line[key]
            current_line = updated_code_lines[key+instruction_nb]
            nb_spaces = len(current_line) - len(current_line.lstrip())
            updated_code_lines[key+instruction_nb] = " "*nb_spaces + 'pass'
        updated_code_lines = ["    "+line if i != 0 else line for i, line in enumerate(updated_code_lines)]
        return updated_code_lines, updated_model_by_line

    def extract_and_evaluate(self, text, context):
        results = []        
        matches = re.finditer(self.pattern, text)
        for match in matches:
            var_name = match.group(1)
            var_type = match.group(2)
            f_prefix = match.group(3)
            value = match.group(5)
            annotation = match.group(6)
            if f_prefix == 'f':
                try:
                    evaluated_value = eval(f'f"{value}"', {}, context)
                except Exception as e:
                    evaluated_value = f"Eval Error: {e}"
            else:
                evaluated_value = value

        results.append(NoesisModel(var_name,var_type,evaluated_value,annotation))

        return results[0]


    def clean_code(self, code):
        source = inspect.cleandoc(code)
        source = re.sub(r'""".*?"""', '', source, flags=re.DOTALL)
        source = re.sub(r'#.*', '', source)
        source = "\n".join([line for line in source.splitlines() if line.strip()])
        source = re.sub(r'def\s+\w+\(.*?\):', '', source)
        return source

    