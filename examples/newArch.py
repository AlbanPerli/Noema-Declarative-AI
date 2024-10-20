class Horizon:
    def __init__(self, *args):
        self.variables = {}
        self.elements = args

    def constituteWith(self, subject):
        for element in self.elements:
            if isinstance(element, Var):
                self.variables.update(element.variables)
            elif isinstance(element, Sentence):
                for key, val in element.sentence.items():
                    self.variables[key] = val
        return self

    def __getattr__(self, name):
        return self.variables.get(name, f"'{name}' not defined")

    def evaluate(self):
        # Évalue toutes les chaînes différées
        for key, value in self.variables.items():
            if isinstance(value, str) and '{' in value:  # Une simple condition pour détecter une f-string
                self.variables[key] = value.format(**self.variables)


class Var:
    def __init__(self, **kwargs):
        self.variables = kwargs


class Sentence:
    def __init__(self, **kwargs):
        self.sentence = kwargs

class Subject:
    def __init__(self):
        pass
        
subject = Subject()
# Exemple d'utilisation
subject = Horizon(
    Var(thought="Time is the only problem"),
    Sentence(thought_explanation="Explain why {thought}."),
    Sentence(thought2="{thought_explanation} oinon {thought}"),
    
).constituteWith(subject)

# Accéder à la propriété thought_explanation
print(subject.thought_explanation)  # Résout la chaîne différée en utilisant la valeur de thought
