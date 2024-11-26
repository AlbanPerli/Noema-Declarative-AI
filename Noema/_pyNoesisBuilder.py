

import ast
import inspect
from io import StringIO
import re
import tokenize

from Noema._noesisModel import NoesisModel
from Noema._patternBuilder import PatternBuilder


class PyNoesisBuilder:
    
    pattern = PatternBuilder.instance().noesis_pattern
    
    def __init__(self):
        pass
        
    def build_noesis(self, description, sender=None):
        ref_code_lines = []
        ref_model_by_line = {}
#         noesis = """[SYSTEM] You are functioning like an hybrid of an Assistant and a python interpreter.
# For the python interpreter, instructions are provided in the form of a python program.
# For the Assistant, special instruction begins with #TASK_NAME: followed by the instruction that needs to be executed.
# [/SYSTEM]"""
        noesis = ""
        source = inspect.getsource(description)        
        system_prompt = inspect.getdoc(description)
        noesis += "\n<s>[INST]"+system_prompt+"\nYou are functionning in a loop of though. Your response can be multiline. Here is the reasonning you are currently executing:\n\n"
        source = self.clean_code(source)
        code_lines = source.splitlines()
        code_lines = [line for line in code_lines if line.strip()]
        ref_code_str = "\n".join(code_lines)
        ref_code_str,models = self.extract_fill_declarations_ast(ref_code_str)
        ref_model_by_line.update(models)
        code_lines = ref_code_str.splitlines()
        ref_code_lines = code_lines
        marks = []
        context = {"self":sender}
            
        for i in range(len(code_lines)):
            line = code_lines[i]
            current_indent = len(line) - len(line.lstrip())
            indent_discrete = 0
            line = line.strip()
            if i in ref_model_by_line:
                model = ref_model_by_line[i]
                noesis += f"{model.display_var()} {model.value[0]}\n"
            elif re.match(self.pattern, line):
                model = self.extract_and_evaluate(line,context)
                if model.annotation != None:
                    pass
                if model.value[-1] not in ['.', '!', '?']:
                    model.value += '.'
                noesis += f"{model.display_var()} {model.value}\n"
                ref_model_by_line[i] = model
                
            # else:
            #    noesis += " "*current_indent+ f"{line}\n"
        noesis += "[/INST]\n\n"
        updated_code, updated_model = self.update_code(ref_code_lines, ref_model_by_line)
        for key in updated_model:
            if key+1 in updated_model:
                updated_model[key].next_model = updated_model[key+1]
                
        return {"noesis":noesis, "code_ref":ref_code_lines, "model_ref":ref_model_by_line, "code_updated":updated_code, "model_updated":updated_model, "marks":marks}
    
    
    def update_code(self, ref_code_lines, ref_model_by_line):
        updated_model_by_line = {}
        updated_code_lines = ["def updated_description(self):"]
        for key in ref_model_by_line:
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

    def extract_fill_declarations_ast(self, code):
        tree = ast.parse(code) 
        results = {}
        lines = code.splitlines()
        updated_lines = lines.copy()

        class FillVisitor(ast.NodeVisitor):
            def visit_AnnAssign(self, node):
                if (
                    isinstance(node.annotation, ast.Name)
                    and node.annotation.id == 'Fill'
                    and isinstance(node.value, ast.Tuple)
                ):
                    variable_name = node.target.id

                    start_line = node.lineno - 1 
                    end_line = node.end_lineno - 1 
                    line_to_remove = updated_lines[start_line:end_line + 1]

                    original_line = lines[start_line]
                    indent = original_line[:len(original_line) - len(original_line.lstrip())]

                    tuple_lines = lines[start_line:end_line + 1]

                    tuple_content = '\n'.join(tuple_lines)
                    open_paren_idx = tuple_content.find('(')
                    close_paren_idx = tuple_content.rfind(')')
                    tuple_content = tuple_content[open_paren_idx + 1 : close_paren_idx]
                    
                    try:
                        values = self.extract_tuple_strings(tuple_content)
                    except ValueError as ve:
                        print(f"Erreur lors de l'extraction des chaînes : {ve}")
                        return

                    fill = values[1]
                    white_list = PatternBuilder.instance().whiteListNames()
                    for type_name in white_list:
                        fill = re.sub(
                            r"\{" + type_name + r"(:[_a-zA-Z][_a-zA-Z0-9]*)?\}",
                            r"##" + type_name + r"\1##",
                            fill,
                        )
                    pattern = r"(?P<static>[^\#]+)|##(?P<type>\w+)(?::(?P<name>\w+))?##"
                    matches = re.finditer(pattern, fill)
                    elements = {}
                    full_response = ""
                    var_and_values = {}
                    for match in matches:
                        static_part = match.group("static")
                        type_name = match.group("type")
                        var_name = match.group("name")
                        if var_name != None:
                            var_and_values[var_name] = None
                        
                    model = NoesisModel(variable_name, "Fill", values, var_and_values=var_and_values)
                    results[start_line] = model
                    
                    for i in range(len(updated_lines)):
                        if updated_lines[i] in line_to_remove:
                            updated_lines[i] = f"{indent}pass"
                    
            def extract_tuple_strings(self, tuple_content):
                tuple_str = f"({tuple_content})"
                tokens = tokenize.generate_tokens(StringIO(tuple_str).readline)
                strings = []
                for toknum, tokval, _, _, _ in tokens:
                    if toknum == tokenize.STRING:
                        if tokval.startswith(('f"', "f'", 'F"', "F'")):
                            tokval = tokval[1:]
                        elif tokval.startswith(('u"', "u'", 'U"', "U'")):
                            tokval = tokval[1:]
                        elif tokval.startswith(('r"', "r'", 'R"', "R'")):
                            tokval = tokval[1:]
                        elif tokval.startswith(('fr"', "fr'", 'FR"', "FR'")):
                            tokval = tokval[2:]
                        elif tokval.startswith(('rf"', "rf'", 'RF"', "RF'")):
                            tokval = tokval[2:]
                        if tokval.startswith('"""') and tokval.endswith('"""'):
                            s = tokval[3:-3]
                        elif tokval.startswith("'''") and tokval.endswith("'''"):
                            s = tokval[3:-3]
                        elif tokval.startswith('"') and tokval.endswith('"'):
                            s = tokval[1:-1]
                        elif tokval.startswith("'") and tokval.endswith("'"):
                            s = tokval[1:-1]
                        else:
                            s = tokval  
                        strings.append(s)
                if len(strings) != 2:
                    raise ValueError("Fill object must contain exactly two strings")
                return tuple(strings)

        FillVisitor().visit(tree)
        updated_lines = [line for line in updated_lines if line.strip()]
        return "\n".join(updated_lines), results
    
    
    

    def extract_and_evaluate(self, text, context):
        results = []        
        matches = re.finditer(self.pattern, text)
        for match in matches:
            var_name = match.group(1)  
            var_type = match.group(2)  
            f_prefix = match.group(3)  
            value = match.group(5)     
            annotation_name = match.group(6)  
            annotation_args = match.group(7)

            if f_prefix == 'f':
                evaluated_value = value
                # try:
                #     evaluated_value = eval(f'f"{value}"', {}, context)
                # except Exception as e:
                #     evaluated_value = f"Eval Error: {e}"
            else:
                evaluated_value = value

            if annotation_name:
                if annotation_args:
                    annotation = f"{annotation_name}({annotation_args})"
                else:
                    annotation = annotation_name
            else:
                annotation = None

            results.append(NoesisModel(var_name, var_type, evaluated_value, annotation))

        return results[0] if results else None


    def clean_code(self, code):
        source = inspect.cleandoc(code)
        source = re.sub(r'"""(.*?)"""', '', source, count=1, flags=re.DOTALL)
        source = re.sub(r'#.*', '', source)
        source = "\n".join([line for line in source.splitlines() if line.strip()])
        source = re.sub(r'def\s+\w+\(.*?\):', '', source)
        return source

    
    
    