from Noema import *

@Noema
def simple_task(task, parameters):
    """You are an incredible Python developer.
    Always looking for the best way to write code."""
    task_to_code = Information(f"I want to {task}")
    formulation = Sentence("Reformulate the task to be easily understood by a Python developer.")
    decomposition = ListOf(Sentence,"Decompose the task into smaller sub-tasks.")
    result = SemPy(formulation.value)(parameters) 
    return result.value
    
Subject("../Models/EXAONE-3.5-7.8B-Instruct-Q4_K_M.gguf",verbose=True)
nb_letter = simple_task("Count the occurence of letters in a word", "strawberry")
print(nb_letter)