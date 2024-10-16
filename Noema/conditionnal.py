from .returnStep import Return
from .step import *
from .var import Var
from .subject import *

class IF(FlowStep):
    def __init__(self, condition, steps_if_true, ELSE=None):
        super().__init__("IF")
        self.condition = condition  # Peut être une chaîne de caractères ou un objet Step
        self.steps_if_true = steps_if_true
        self.steps_if_false = ELSE or []
        self.condition_description = self._describe_condition()

    def _describe_condition(self):
        """Retourne une description lisible de la condition."""
        if isinstance(self.condition, str):
            # Si la condition est une chaîne de caractères, c'est une expression simple
            return self.condition
        elif isinstance(self.condition, Step):
            # Si la condition est un Step, on utilise son nom pour la description
            return f"Condition Step: {self.condition.name}"
        else:
            return "Unknown Condition"

    def list_steps(self,state):
        for step in self.steps_if_true:
            if isinstance(step, Var):
                step.execute(state,False)
        for step in self.steps_if_false:
            if isinstance(step, Var):
                step.execute(state,False)
                
        step_names = [f"{self.name} (Condition: {self.condition_description})"]
        step_names.append("  IF True:")
        for step in self.steps_if_true:
            step_names.extend(['    ' + sub_step for sub_step in step.list_steps(state)])
        if self.steps_if_false:
            step_names.append("  ELSE:")
            for step in self.steps_if_false:
                step_names.extend(['    ' + sub_step for sub_step in step.list_steps(state)])
        return step_names

    def evaluate_condition(self, state):
        """
        Évalue la condition. Elle peut être :
        - Une chaîne de caractères : évaluée avec les valeurs de l'état.
        - Un Step : la méthode `execute` est appelée et son résultat est utilisé.
        """
        # Si la condition est une chaîne de caractères, évaluer en utilisant l'état
        if isinstance(self.condition, str):
            current_condition = self.extract_variables_from_string(self.condition, state)
            print(f"Current condition: {current_condition}")
            try:
                return eval(current_condition, {})
            except Exception as e:
                print(f"Error evaluating condition: {e}")
                return False
        # Si la condition est un Step, exécuter le Step
        elif isinstance(self.condition, Step):
            # On suppose que le Step retourne un booléen dans son exécution
            result = self.condition.execute(state)
            return bool(result)
        else:
            raise ValueError("Condition must be a string or a Step instance")

    def execute(self, state):
        outputs = []
        if self.evaluate_condition(state):
            for step in self.steps_if_true:
                if isinstance(step, Return):
                    return step.execute(state)
                else:
                    step.execute(state)
        else:
            for step in self.steps_if_false:
                if isinstance(step, Return):
                    return step.execute(state)
                else:
                    step.execute(state)
                    
