from Noema import *

class SmartAgent:

    def __init__(self,task) -> None:
        self.task = task
        
    @Noema
    def think(self):
        """You are a smart agent. You have a task to perform."""
        task = Information(f"{self.task}")
        p1 = SemPy("Find the place of a letter in a word.")("hello world","o")
        print(p1.value)
        p2 = SemPy("Ordering the list alphabetically.")(["hello","world","python","java","swift"])
        print(p2.value)

        # task_type = SelectOrNone("What is the type of the task?", options=["Programming","Design","Writing","Other"])
        # note = Int("Provide a note between 0 and 10 about the task.")
        # selected_word = Word("Display the selected type of task.")
        # if not task_type.value:
        #     return "Unknown task type"
        # else:
        #     l = []
        #     for i in range(2):
        #         reflexion = Sentence("Providing a reflexion about the task.")
        #         #consequence = self.consequence(reflexion)
        #         evaluate = Sentence("Evaluating the consequence.")
        #         point_of_view = Sentence("Providing a new point of view about the task.")

        #     point_of_view_list = ListOf(Sentence, f"Listing all the previous point_of_view.", 5)
        #     conclusion = Paragraph("Providing a conclusion which is a synthesis of the previous steps.")

        #     return conclusion.value 
    
    @Noema
    def consequence(self, reflexion):
        """
        You have to think about the consequence of your reflexion.
        Slowy, step by step.
        """
        resuming = Sentence("Resuming the reflexion.")
        analysis = Sentence("Analysing the consequence of this reflexion")
        loop = Information("I will loop over the consequence chain.")
        for i in range(4):
            consequence = Sentence(f"Writing the consequence {i}",i)
            step = Int("Writing the step number.")
            finished = Bool("Is the chain finished?",i)
            if finished.value == True:
                break
        conclusion = Sentence("Provide a conclusion about the consequences")
        note = Float("Provide a note between 0 and 10 about the consequence.")
        
        return conclusion.value

Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf",verbose=True)
smartAg = SmartAgent("Write the code of a to do list in swiftui. Je m'appelle Jean Dupont et j'ai une adresse email gmail. Nous sommes le 12/12/2021.")
conclusion = smartAg.think()
print(Subject().shared().llm)