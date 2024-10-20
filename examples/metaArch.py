
class Horizon:
    pass
class Var:
    pass
class Sentence:
    pass
class Int:
    pass
class IF:
    pass
class Select:
    pass
class Foreach:
    pass

s = Horizon(
    Var(thought = "Time is the only problem"),
    Sentence(thougth_explanation = f"Explain why '{s.thougth}'."), # The sentence produced is stored in {thougth_explanation}
    Int(explanation_note="Give a note between 0 and 10 to qualify the quality of your explanation."), # The model produce an python integer that is stored in {explanation_note}
    
    Foreach(s.thought,[ # item / idx
         Sentence(thougth_explanation_idx = f"Explain why '{s.item}' is No {s.idx}."),
         Sentence(tutu_idx = f"Explain why '{s.item}' is No {s.idx}."),
    ])
    
    IF(s.explanation_note < 5, [
        Select(auto_analysis="Do some auto-analysis, and choose a word to qualify your note", options=["Fair","Over optimistic","Neutral"]),
    ],ELSE=[
       Select(auto_analysis="Do some auto-analysis, and choose a word to qualify your note", ["Over optimistic","Neutral"]),
       IF(s.auto_analysis == 'Over optimistic', [
            Int(points_to_remove="How many points do you think you should remove to be fair?"),
            Sentence(points_explanation= f"Explain why you think you should remove {s.points_to_remove} points."),
       ])
    ])
).constituteWith(s)
