from .generators import *
from .step import Step

class Reflexion(Step):
    
    def __init__(self, goal:str, reflexion_var:str, informations:str = None, action=None):
        if not re.match(r'\{(\w+)\}', reflexion_var) and not re.match(r'\{\{(\w+)\}\}', reflexion_var):
                raise ValueError(f"La source de donnée {reflexion_var} doit être une variable entre accolades.")
        super().__init__(name="Reflexion: ", action=action)
        self.value = goal
        self.reflexion_var = reflexion_var
        self.informations = informations
        
    def execute(self, state):
        current_value = self.extract_variables_from_string(self.value, state)
        current_reflexion_var = self.extract_variables_from_string(self.reflexion_var, state)
        if re.match(r'\{(\w+)\}', self.reflexion_var):
            current_reflexion_var = re.findall(r'\{(\w+)\}', self.reflexion_var)[0]
        prompt = ""
        if self.informations:
            current_datasource_str = self.extract_variables_from_string(self.informations, state)
            prompt += f"""
Informations pour la réflexion :
{current_datasource_str}
"""

        prompt += f"""[INST]Tu fonctionnes dans une boucle de pensées.
Tu utilises le format suivant :
But général: le but général de la réflexion.
REFLEXION: tu penses au sujet que tu dois traiter.
PLAN: tu élabores un plan pour répondre à la question posée.
OBSERVATION: tu observes les éléments qui te permettent de répondre à la question posée.
ANALYSE: tu analyses les éléments observés au regard des règles et informations que tu as.
PROPOSITION: tu formules une proposition de réponse.
FIN: tu détermines si tu as finis de réfléchir au problème posé. Tu réponds par Oui ou Non
... (cette boucle REFLEXION/PLAN/OBSERVATION/FIN peut se répéter N fois tant que tu n'as pas atteint l'objectif)
Pensée N : J'ai maintenant toutes les informations pour répondre à la question de départ de manière exhaustive.
Fait.
[/INST]

But général: {self.value}
"""     
        tmp_copy = str(state.llm)
        lm = state.llm
        lm.reset()
        lm += prompt + gen(name="reflexion",stop=["Fait.",'</s>','Pensée N :'],max_tokens=500)

        reflexion_value = lm["reflexion"]
        state.set(current_reflexion_var, reflexion_value)
        lm.reset()
        state.llm += tmp_copy
        return current_value
    
    def list_steps(self,state):
        """Retourne la liste des steps à exécuter, ici c'est seulement un step"""
        return [self.name+" "+self.value] if self.should_include_in_list() else []
