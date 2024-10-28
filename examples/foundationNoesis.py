from Noema import *

s = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf") # Create a subject

find_job_name = Noesis("Find a job name in a field.",["field_name","max_length"],[
    Information("You have to choose a job name in the field of {field_name}."),
    Var(word_length = 0),
    While(lambda: s.word_length < s.max_length, [
        Word(job_name = "Give a good job name:"),
        Int(word_length = "How many letters are in the word {job_name}?"),
        Print("Selected job {job_name}"),
        Information("You have to choose a new job name each time."),
    ]),
    Return("{job_name} is a good job name in the field of {field_name}.") #Return value
])

s = Horizon(
    Constitute(job_name = lambda:find_job_name(s, field_name="IT",max_length=10)), 
    Print("{job_name} has more than 10 letters."),
).constituteWith(s) # The horizon is constituted by the LLM

