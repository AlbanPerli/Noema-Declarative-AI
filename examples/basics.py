from Noema import *

# Create a subject (LLM)
Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf", verbose=True) # Llama cpp model

# Create a way of thinking
class SimpleWayOfThinking:
    
    def __init__(self, task):
        super().__init__()
        self.task = task
        
    @Noema
    def think(self):
        """
        You are a simple thinker. You have a task to perform.
        Always looking for the best way to perform it.
        """
        povs = []
        task = Information(f"{self.task}") # inject information to the LLM
        for i in range(2):
            step_nb = i + 1
            reflexion = Sentence("Providing a reflexion about the task.", step_nb)
            consequence = Sentence("Providing the consequence of the reflexion.", step_nb)
            evaluate = Sentence("Evaluating the consequence.", step_nb)
            point_of_view = Sentence(f"Providing a point of view about the task different than {povs}", step_nb)
            point_of_view_qualification = Word(f"Qualifying the point of view, must choose a word different of: {povs}", step_nb)
            povs.append(point_of_view_qualification.value)
            creativitity_level = Float(f"How creative is this point of view: {povs[-1]}. (Between 0-10)", step_nb)            
            if creativitity_level.value < 8.0:
                important = Information("I need to be more creative!")
        conclusion = Paragraph("Providing a conclusion which is a synthesis of the previous steps.")
        return conclusion.value # return the conclusion value
    
 
swot = SimpleWayOfThinking("How to write a good iOS application?")
conclusion = swot.think()
print(conclusion)
print(Subject().shared().noema())

