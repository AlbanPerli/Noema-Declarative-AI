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
        The application will be built with SwiftUI, respecting the good practices.
        The class names will follow the iOS naming convention, the files names will be the same as the classname.
        """
        goal:Information = f"{self.value}"
        reflexion:Sentence = "Think about the architecture of the application." @Reflexion
        view_list:list[Word] = "Give the name of the views and models of the application. Each name follow the iOS standard naming."  @Reflexion
        model:list[Word] = "Give the name of the models." 
        file_names:list[Word] = "Give a file name (with extension) for each file."
        generated_code = [] 
        for file in file_names.value:
            though_about_code:Paragraph = "Think about the code for the file {file}." @Reflexion
            code_for_file:Swift = "Generate the SwiftUI code for the file {file}"
            generated_code.append(code_for_file.value)
        
        full_code = " ".join(generated_code)
        fixed_code:Swift = "Read the entire code: {full_code}, fix the issues and write the final version of the code."
        user_input = None
        while True:
            user_input = input("Enter 'Done' when you are finished.")
            if user_input == "Done":
                break
            else:
                fixed_code:Swift = "Apply the following changes:{user_input}\nTo the code: {fixed_code.value}"
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


subject = Subject("../Models/Codestral-22B-v0.1-Q3_K_M.gguf")#Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")
subject.add_capabilities("capabilities")
# Utilisation
archi = iOSArchitect(name="Toto", value="Build an iOS application that displays a list of items. If you click on an item, you can see the details of the item. Items are generated locally only.").go(subject)
print("\n\n")
print(subject.llm)

