from Noema import *

s = Subject("path_to_model.gguf")
s.add(thougth = "Time is the only problem") # store "Time is the only problem" in thougth

s = Horizon(
    Var(final_thought=None), # Create a variable final_thought
    Sentence(thougth_explanation = "Explain why '{thougth}'."), 
    Int(explanation_note = "Give a note between 0 and 10 to qualify the quality of your explanation."), 
    Select(auto_analysis="Do some auto-analysis, and choose a word to qualify your note", options=["Fair","Over optimistic","Neutral"]),
    IF(lambda: s.explanation_note < 5, [
        Information("The explanation is not clear enough, and the note is too low."),
        Int(points_to_add = "How many points do you think you should add to be fair?"),
        Sentence(points_explanation = "Explain why you think you should add {points_to_add} points."),
        Var(final_thought = "The explanation is not clear enough, and the note is too low. I should add {points_to_add} points."),
    ],ELSE=[
       IF(lambda: s.auto_analysis == 'Over optimistic', [  
            Int(points_to_remove ="How many points do you think you should remove to be fair?"),
            Sentence(points_explanation = "Explain why you think you should remove {points_to_remove} points."),
            Var(final_thought = "The explanation is not clear enough, and the note is too low. I should remove {points_to_remove} points."),
       ],ELSE=[
            Print("The explanation is clear enough, and the note is fair."),   
            Var(final_thought = "The note is fair."),
        ]),
    ])
).constituteWith(s) # The horizon is constituted by the LLM

print(s.final_thought) # Print the final thought