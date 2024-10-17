from Noema import *

subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")
subject.add(Var("Time is the only problem", "{thougth}")) # store "Time is the only problem" in {thougth}

subject = Horizon(
    Information("You have to choose a job name."),
    Var(0,"{word_length}"),
    While("{word_length} < 7",[
        Word("Give a good job name:","{job_name}"),
        Int("How many letters are in the word {job_name}?","{word_length}"),
        Print("Selected job {job_name}"),
        Information("You have to choose a new job name each time."),
    ]),
    Print("The word {job_name} has more than 10 letters."),
    PrintNoema()
).constituteWith(subject)

# subject = Horizon(
#     Sentence("Explain why '{thougth}'.","{thougth_explanation}"), # The sentence produced is stored in {thougth_explanation}
#     Int("Give a note between 0 and 10 to qualify the quality of your explanation.","{explanation_note}"), # The model produce an python integer that is stored in {explanation_note}

#     IF("{explanation_note} < 5", [
#         Select("Do some auto-analysis, and choose a word to qualify your note", ["Fair","Over optimistic","Neutral"], "{auto_analysis}"),
#     ],ELSE=[
#        Select("Do some auto-analysis, and choose a word to qualify your note", ["Over optimistic","Neutral"], "{auto_analysis}"),
#        IF("'{auto_analysis}' == 'Over optimistic'", [
#             Int("How many points do you think you should remove to be fair?","{points_to_remove}"),
#             Sentence("Explain why you think you should remove {points_to_remove} points.","{points_explanation}"),
#        ])
#     ])
# ).constituteWith(subject)

# print(subject.data["auto_analysis"])
# print(subject.data["points_to_remove"])
# print(subject.data["points_explanation"])