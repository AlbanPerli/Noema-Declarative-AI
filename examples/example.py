from Noema import *

subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")
subject.add(Var("Time is the only problem", "{thougth}")) # store "Time is the only problem" in {thougth}

subject = Horizon(
    ListOf("What are the problems you are facing (in order of difficulty)?","{problems}",Sentence), # The model produce a list of sentence that is stored in {problems}
    ForEach("{problems}","{item}","{count}", [
        Sentence("Explain why '{item}' is the problem No {count}.","{item_explanation}"), # The sentence produced is stored in {item_explanation}
        Print("Pb Nb {count}: {item}. Explanation: {item_explanation}")
    ])
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

print(subject.noema)
print("***")
# print(subject.data["auto_analysis"])
# print(subject.data["points_to_remove"])
# print(subject.data["points_explanation"])