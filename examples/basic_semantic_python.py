import _bootstrap
from Noema import *
from _config import create_subject, run_example

@Noema
def simple_task(task, parameters):
    """You are an incredible Python developer.
    Always looking for the best way to write code."""
    task_to_code = Information(f"I want to {task}")
    reformulation = Sentence("Reformulate the task to be easily understood by a Python developer.")
    decomposition = ListOf(Sentence,"Decompose the task into smaller sub-tasks.")
    result = SemPy(reformulation.value)(parameters) 
    return result.value
    
def main():
    create_subject("/Users/al/Documents/IA/Models/LLM/LFM2.5-8B-A1B-Q4_K_M.gguf")
    nb_letter = simple_task("Count the occurence of letters in a word", "strawberry")
    print(nb_letter)


run_example(main)
