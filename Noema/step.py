import re

class Step:
    def __init__(self, name):
        self.name = name
        self.output = None
        
    def execute(self, state):
        pass

    def replace_variables(self, string, state, can_be_None):
        def lookup_reference(match):
            ref_variable = match.group(1) 
            referenced_var_name = state.get(ref_variable, None)
            if referenced_var_name:
                return str(state.get(referenced_var_name, match.group(0)))  
            return match.group(0) 
        
        string = re.sub(r'\{\{(\w+)\}\}', lookup_reference, string)

        def lookup_variable(match):
            var_name = match.group(1)
            value = state.get_prop(var_name)
            print("Value: ", value)
            if value is not None:
                return str(value)
            else:
                if can_be_None:
                    return match.group(0)
                else:
                    raise ValueError(f"The variable {var_name} is not defined.")

        string = re.sub(r'\{(\w+)\}', lookup_variable, string)

        if re.search(r'\{(\w+)\}', string):
            string = re.sub(r'(.*)\{(\w+)\}(.*)', r'\1\2\3', string)
        
        print("String: ", string)
        return string

    def extract_variables_from_string(self, string, state, can_be_None = False):
        return self.replace_variables(string, state, can_be_None)

    def list_steps(self, state):
        return [self.name] if self.should_include_in_list() else []

    def should_include_in_list(self):
        return True

class FlowStep(Step):
    
    def __init__(self, name):
        super().__init__(name)


class GenStep(Step):
    def __init__(self, llm_input:str, step_name:str , output_type:str):
        if isinstance(step_name, str):
            super().__init__(step_name)
        elif isinstance(step_name, Step):
            super().__init__(step_name.name)
        else:
            raise ValueError("The parameter must be a state key or a Step.")
        self.step_name = step_name
        self.output_type = output_type
        self.llm_input = llm_input
        self.current_llm_input = None
        self.display_step_name = "#"+step_name.upper()+": "
        self.display_type = ""
        
    def _to_function(self, value):
        return lambda: value

    def execute(self, state):
        if isinstance(self.step_name, str):
            if re.match(r'\{\{(\w+)\}\}', self.step_name):
                self.display_step_name = "#"+self.extract_variables_from_string(self.step_name, state).upper()+": "
        else:
            raise ValueError("The parameter name must be a keys")
        self.current_llm_input = self.extract_variables_from_string(self.llm_input, state)

    def list_steps(self,state):
        if isinstance(self.step_name, Step):
            current_step_name = self.step_name.execute(state)
            current_step_name = self.extract_variables_from_string(current_step_name, state)
            return ["#"+current_step_name.upper()+": "+self.llm_input] if self.should_include_in_list() else []
        elif isinstance(self.step_name, str):
            return ["#"+self.name.upper()+": "+self.llm_input] if self.should_include_in_list() else []
        else:
            raise ValueError("The parameter must be a string (state key) or a Step.")


    def should_include_in_list(self):
        return True 
    
    
class DebugStep(Step):
    def __init__(self, name):
        super().__init__(name)

    def execute(self, state):
        pass

    def list_steps(self):
        return [self.name] if self.should_include_in_list() else []

    def should_include_in_list(self):
        return False  
