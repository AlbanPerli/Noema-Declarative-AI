from Noema import *
import re
from capabilities import *

class iOSArchitect(Noesis):
    
    def __init__(self, name, value):
        super().__init__()
        self.name = name
        self.value = value
    
    def description(self):
        """
        You are an iOS architect. You are responsible for architecture of the iOS application.
        """
        goal:Information = f"{self.value}"
        reflexion:list[Sentence] = "Retreive all the steps composing the architecture of the application" @Reflexion
        how_many_view:Int = "Think about how many views are needed by the application." @Reflexion
        view_list:list[Word] = "List the name of the {how_many_view.value} views of the application."  @Reflexion
        for view in view_list.value:
            ideas_list:list[Sentence] = "List ideas of new functionnalities for {view}."
        # if how_many_view.value > 1:
        #     print("You will need a navigation controller.")
        # steps:Information = ["the interface","the network call", "the database"] 
        # code_by_step = {}
        # for step in steps:
        #     print(step)
        #     step_explanation:Sentence = "Explain the implications of {step}." 
        #     class_name:Word = "Following the good practice, find a name for the class that will handle {step}." @Reflexion
        #     file_creation:Sentence = "Create a file for the class that will handle {step}." 
        #     model_name:Word = "Following the good practice, find a model class name for the model that will handle {step}." @Reflexion
        #     file_creation:Sentence = "Create a file for the class that will handle {step}."
            
        #return code_by_step


subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")
# Utilisation
archi = iOSArchitect(name="Toto", value="You want to build an iOS application that displays a list of items. If you click on an item, you can see the details of the item.").go(subject)
print("\n\n")
print(subject.llm)

