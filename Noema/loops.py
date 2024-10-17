from .var import Var
from .step import *
from .subject import *

class Repeat(Step):
    def __init__(self, count, steps):
        super().__init__("Repeat")
        """
        :param count: Le nombre de répétitions, soit un entier, soit un Step qui génère un entier.
        :param steps: La liste des étapes à exécuter pour chaque répétition.
        """
        self.count = count  # Peut être un entier, un Step ou une string
        if isinstance(count,str):
            if not re.match(r'\{(\w+)\}', count):
                raise ValueError(f"La source de donnée {count} doit être une variable entre accolades.")
            unwrapped_count = re.findall(r'\{(\w+)\}', count)[0]
            self.count = unwrapped_count
        
        self.steps = steps
        
    def list_steps(self,state):
        step_names = [f"{self.name} (x{self.count})"]
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def get_count(self, state):
        """
        Récupère le nombre de répétitions, soit depuis un entier, soit depuis l'exécution d'un Step.
        :param state: L'état courant.
        :return: Le nombre de répétitions (entier).
        """
        # Si count est un entier
        if isinstance(self.count, int):
            return self.count
        
        elif isinstance(self.count,str):
            return state.get(self.count)

        # Si count est un Step
        elif isinstance(self.count, Step):
            count = self.count.execute(state)
            if not isinstance(count, int):
                raise ValueError("The Step must return an integer.")
            return count
        
        else:
            raise ValueError("The count must be either an integer,Step that returns an integer or a variable name")

    def execute(self, state):
        repetitions = self.get_count(state)
        for i in range(repetitions):
            for step in self.steps:
                step.execute(state)
                
class ForEach(Step):
    def __init__(self, source, item_name, counter_name, steps):
        if not re.match(r'\{(\w+)\}', item_name):
            raise ValueError(f"La source de donnée {item_name} doit être une variable entre accolades.")
        unwrapped_item_name = re.findall(r'\{(\w+)\}', item_name)[0]
        
        if not re.match(r'\{(\w+)\}', counter_name):
            raise ValueError(f"The datasource {counter_name} must be a variable between curly braces.")
        unwrapped_counter_name = re.findall(r'\{(\w+)\}', counter_name)[0]

        super().__init__("Foreach")
        self.source = None
        if isinstance(source,str):
            if not re.match(r'\{(\w+)\}', source):
                raise ValueError(f"The datasource {source} must be a variable between curly braces.")
            self.source = re.findall(r'\{(\w+)\}', source)[0]
        else:
            self.source = source  # Peut être une clé d'état ou un Step
        self.item_name = unwrapped_item_name
        self.counter_name = unwrapped_counter_name
        self.steps = steps
        self.source_description = self._describe_source()

    def _describe_source(self):
        if isinstance(self.source, str):
            return f"State key: {self.source}"
        elif isinstance(self.source, Step):
            return f"Step: {self.source.name}"
        else:
            return "Unknown Source"

    def list_steps(self,state):
        for step in self.steps:
            if isinstance(step, Var):
                step.execute(state,False)
                
        step_names = [f"{self.name} (Source: {self.source_description}, Item: {self.item_name}, Counter: {self.counter_name})"]
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def execute(self, state):
        # Récupérer la liste d'éléments à partir de la source (clé ou Step)
        items = self.get_items(state)
        
        # Pour chaque élément de la liste, l'associer au nom donné (item_name) et exécuter les étapes
        for index, item in enumerate(items):
            # Stocker l'élément courant temporairement dans l'état
            state.set(self.item_name, item)
            state.set(self.counter_name, index+1)
            
            # Exécuter les étapes pour chaque élément
            for step in self.steps:
                step.execute(state)

    def get_items(self, state):
        if isinstance(self.source, str):
            items = state.get(self.source, [])
            if not isinstance(items, list):
                raise ValueError(f"The state key '{self.source}' must contain a list.")
            return items

        elif isinstance(self.source, Step):
            items = self.source.execute(state)
            if not isinstance(items, list):
                raise ValueError("The Step must return a list.")
            return items
        
        else:
            raise ValueError("The source must be either a string (state key) or a Step that returns a list.")
        
        
        
class While(Step):
    def __init__(self, condition, steps):
        super().__init__("While")
        self.condition = condition
        self.steps = steps
        self.condition_description = self._describe_condition()

    def _describe_condition(self):
        if isinstance(self.condition, str):
            return self.condition
        elif isinstance(self.condition, Step):
            return "Repeat:"#f"Condition Step: {self.condition.name}"
        else:
            return "Unknown Condition"

    def list_steps(self,state):
        for step in self.steps:
            if isinstance(step, Var):
                step.execute(state,False)
                
        step_names = ["Repeat the following instructions:"] #[f"{self.name} (Condition: {self.condition_description})"]
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def execute(self, state):
        out_condition = True
        while out_condition:
            for step in self.steps:
                step.execute(state)
            out_condition = self.evaluate_condition(state)

    def evaluate_condition(self, state):
        print("EVALUATING CONDITION")
        if isinstance(self.condition, str):
            current_condition = self.extract_variables_from_string(self.condition, state)
            try:
                return eval(current_condition, {})
            except Exception as e:
                print(f"Error evaluating condition: {e}")
                return False
        elif isinstance(self.condition, Step):
            res = self.condition.execute(state)
            print(f"Condition result: {res}")
            return bool(res)
        else:
            raise ValueError("Condition must be either a string or a Step.")

# TODO: Find a better way...
class WhileNot(Step):
    def __init__(self, condition, steps):
        super().__init__("While")
        self.condition = condition
        self.steps = steps
        self.condition_description = self._describe_condition()

    def _describe_condition(self):
        if isinstance(self.condition, str):
            return self.condition
        elif isinstance(self.condition, Step):
            return "Repeat:" #f"Condition Step: {self.condition.name}"
        else:
            return "Unknown Condition"

    def list_steps(self,state):
        for step in self.steps:
            if isinstance(step, Var):
                step.execute(state,False)
                
        step_names = [f"{self.name} (Condition: {self.condition_description})"]
        for step in self.steps:
            step_names.extend(['  ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def execute(self, state):
        out_condition = False
        while not out_condition:
            for step in self.steps:
                step.execute(state)
            out_condition = self.evaluate_condition(state)

    def evaluate_condition(self, state):
        print("EVALUATING CONDITION")
        if isinstance(self.condition, str):
            current_condition = self.extract_variables_from_string(self.condition, state)
            try:
                return eval(current_condition, {})
            except Exception as e:
                print(f"Error evaluating condition: {e}")
                return False
        elif isinstance(self.condition, Step):
            res = self.condition.execute(state)
            print(f"Condition result: {res}")
            return bool(res)
        else:
            raise ValueError("Condition must be either a string or a Step.")
