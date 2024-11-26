from Noema import *

subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")

class WayOfThinking(Noesis):
    
    def description(self):
        """
        You are a specialist in nice house building.
        """
        builder:Reflexion = "How to build a house in the forest?"
        print("Noesis:")
        print(builder.noesis)
        print("-"*50)
        print("Noema:")
        print(builder.noema)
        print("-"*50)
        print("Value:")
        print(builder.value)
        print("-"*50)

WayOfThinking().constitute(subject)
