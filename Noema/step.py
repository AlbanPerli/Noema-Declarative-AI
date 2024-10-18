import re

class Step:
    def __init__(self, name, action=None):
        self.name = name
        self.action = action  # Une fonction qui prend l'état comme paramètre
        self.output = None
        
    def execute(self, state):
        if self.action:
            self.action(state)


    def replace_double_accolades(self, string, state):
        def lookup_reference(match):
            ref_variable = match.group(1)
            referenced_var_name = state.get(ref_variable, None)
            if referenced_var_name:
                return str(state.get(referenced_var_name, match.group(0))) 
            return match.group(0)  

        return re.sub(r'\{\{(\w+)\}\}', lookup_reference, string)

    def replace_variables(self, string, state):
        def lookup_reference(match):
            ref_variable = match.group(1) 
            referenced_var_name = state.get(ref_variable, None)
            if referenced_var_name:
                return str(state.get(referenced_var_name, match.group(0)))  
            return match.group(0) 
        
        string = re.sub(r'\{\{(\w+)\}\}', lookup_reference, string)

        def lookup_variable(match):
            var_name = match.group(1)
            return str(state.get(var_name, match.group(0)))  

        string = re.sub(r'\{(\w+)\}', lookup_variable, string)

        if re.search(r'\{(\w+)\}', string):
            string = re.sub(r'(.*)\{(\w+)\}(.*)', r'\1\2\3', string)
        
        return string

    def extract_variables_from_string(self, string, state):
        return self.replace_variables(string, state)
    
    def extract_variables_from_string_to_list(self, string, state):
        variable_pattern = re.compile(r"\{([a-zA-Z_][a-zA-Z0-9_]*)\}")

        def extract_variable(match):
            variable_name = match.group(1)
            value = state.get(variable_name)
            return value

        return [extract_variable(match) for match in variable_pattern.finditer(string)]
    

    def list_steps(self, state):
        return [self.name] if self.should_include_in_list() else []

    def should_include_in_list(self):
        return True

class FlowStep(Step):
    
    def __init__(self, name, action=None):
        super().__init__(name, action)

class GenStep(Step):
    def __init__(self, llm_input:str, step_name:str , output_type:str, action=None):
        unwrapped_name = None
        if isinstance(step_name, str):
            if not re.match(r'\{(\w+)\}', step_name) and not re.match(r'\{\{(\w+)\}\}', step_name):
                raise ValueError(f"La source de donnée {step_name} doit être une variable entre accolades.")
            unwrapped_name = re.findall(r'\{(\w+)\}', step_name)[0]
            super().__init__(unwrapped_name, None)
        elif isinstance(step_name, Step):
            unwrapped_name = step_name.name
            super().__init__(unwrapped_name, None)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        self.step_name = step_name
        self.output_type = output_type
        self.llm_input = llm_input
        self.action = action
        self.current_llm_input = None
        self.current_step_name = None
        self.display_step_name = "#"+unwrapped_name.upper()+": "
        self.display_type = ""

    def execute(self, state):
        if isinstance(self.step_name, Step):
            self.current_step_name = self.step_name.execute(state)
            self.current_step_name = self.extract_variables_from_string(self.current_step_name, state)
            self.display_step_name = "#"+self.current_step_name.upper()+": "
            self.name = self.current_step_name
        elif isinstance(self.step_name, str):
            if re.match(r'\{\{(\w+)\}\}', self.step_name):
                self.display_step_name = "#"+self.extract_variables_from_string(self.step_name, state).upper()+": "
                self.current_step_name = self.extract_variables_from_string(self.step_name, state)
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")
        
        self.current_llm_input = self.extract_variables_from_string(self.llm_input, state)

    def list_steps(self,state):
        if isinstance(self.step_name, Step):
            current_step_name = self.step_name.execute(state)
            current_step_name = self.extract_variables_from_string(current_step_name, state)
            return ["#"+current_step_name.upper()+": "+self.llm_input] if self.should_include_in_list() else []
        elif isinstance(self.step_name, str):
            if re.match(r'\{\{(\w+)\}\}', self.step_name):
                return ["#"+self.extract_variables_from_string(self.step_name,state).upper()+": "+self.llm_input] if self.should_include_in_list() else []
            else:
                return ["#"+self.name.upper()+": "+self.llm_input] if self.should_include_in_list() else []
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")


    def should_include_in_list(self):
        return True 
    
    
class DebugStep(Step):
    def __init__(self, action=None):
        super().__init__("Debug", action)

    def execute(self, state):
        if self.action:
            self.action(state)

    def list_steps(self):
        return [self.name] if self.should_include_in_list() else []

    def should_include_in_list(self):
        return False  
