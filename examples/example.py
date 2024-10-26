from Noema import *

s = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf") # Create a subject
s.add(though = "Time is the only problem") # store "Time is the only problem" in thougth
s.add_knowledge("If you have a problem, you can solve it by taking the time to think about it.")
s.add_knowledge("Concerning any arithmetic operation, you have to use tools.")
s.add_capabilities("capabilities") # Load the capabilities from the module capabilities.py

s = Horizon(
    Var(final_thought=None), # Create a variable final_thought
    Knowledge("How to build a house?"),
    PrintNoema(),
    Reflexion(thougth_explanation = "Explain why '{though}'."),
    # Print("Auto-analysis: {auto_analysis}"),

    Int(explanation_note = "Give a note between 0 and 10 to qualify the quality of your explanation."), 
    Select(auto_analysis="Do some auto-analysis, and choose a word to qualify your note", options=["Fair","Over optimistic","Neutral"]),
    IF(lambda: s.explanation_note < 5, [
        Information("The explanation is not clear enough, and the note is too low."),
        Int(points_to_add = "How many points do you think you should add to be fair?"),
        Sentence(points_explanation = "Explain why you think you should add {points_to_add} points."),
        Var(final_thought = "The explanation is not clear enough, and the note is too low. I should add {points_to_add} points."),
    ],ELSE=[
       IF(lambda: s.auto_analysis == 'Over optimistic', [  
            Int(points_to_remove = "How many points do you think you should remove to be fair?"),
            Sentence(points_explanation = "Explain why you think you should remove {points_to_remove} points."),
            Var(final_thought = "The explanation is not clear enough, and the note is too low. I should remove {points_to_remove} points."),
       ],ELSE=[
            Print("The explanation is clear enough, and the note is fair."),   
            Var(final_thought = "The note is fair."),
        ]),
    ]),
    PrintNoesis(),
    PrintNoema()
).constituteWith(s) # The horizon is constituted by the LLM

print(s.final_thought) # Print the final thought