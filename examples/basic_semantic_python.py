from Noema import *

@Noema
def simple_task():
    """Instruct prompt """
    letter_index = SemPy("Find the place of a letter in a word.")("hello world","o") 
    # generate a python function with 2 parameters that follow the instruction `Find the place of a letter in a word.`'
    print(letter_index.value)
    
Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf",verbose=True)
simple_task()