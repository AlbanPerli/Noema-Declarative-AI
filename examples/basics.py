from Noema import *

# Create a subject (LLM)
subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf") # Llama cpp model

# Create a way of thinking
class SimpleWayOfThinking(Noesis):
    
    def __init__(self, task):
        super().__init__()
        self.task = task
        
    # 'description' name is mandatory
    def description(self):
        """
        You are a simple thinker. You have a task to perform.
        Always looking for the best way to perform it.
        """
        
        task:Information = f"{self.task}" # inject information to the LLM
        for i in range(2):
            step:Information = f"{i}" # inject information to the LLM
            reflexion:Sentence = "Providing a reflexion about the task."
            consequence:Sentence = "Providing the consequence of the reflexion."
            evaluate:Paragraph = "Evaluating the consequence."
        
        conclusion:Paragraph = "Providing a conclusion which is a synthesis of the previous steps."
        
        return conclusion.value # return the conclusion value
    

swot = SimpleWayOfThinking("Help me to write a poem.")
conclusion = swot.constitute(subject, verbose=True) # execute the way of thinking
print("-"*50)
print("LLM output:")
print("-"*50)
print(subject)
print("-"*50)
print("Conclusion:")
print("-"*50)
print(conclusion)
print("-"*50)
