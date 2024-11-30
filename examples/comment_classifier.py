from Noema import *

# Create a new Subject
subject = Subject("../Models/Mistral-NeMo-Minitron-8B-Instruct.Q4_K_M.gguf")

# Create a way of thinking
class CommentClassifier(Noesis):
    
    def __init__(self, comments, labels):
        super().__init__()
        self.comments = comments
        self.labels = labels

    def description(self):
        """
        You are a specialist in classifying comments. You have a list of comments and a list of labels.
        You need to provide an analysis for each comment and select the most appropriate label.
        """
        comments_analysis = []
        for c in self.comments:
            comment:Information = f"This is the comment: '{c}'."
            comment_analysis:Sentence = "Providing an analysis of the comment."
            possible_labels:Information = f"Possible labels are: {self.labels}."
            task:Information = "I will provide an analysis for each label."
            reflexions = ""
            for l in self.labels:
                label:Information = f"Thinking about the label: {l}."
                reflexion:Sentence = "Providing a deep reflexion about it."
                consequence:Sentence = "Providing the consequence of the reflexion."
                reflexions += "\n"+reflexion.value
            selected_label:Word = "Providing the label name."
            comment_analysis = {"comment": c, 
                                "selected_label": selected_label.value,
                                "analysis": reflexions}
            comments_analysis.append(comment_analysis)
            
        return comments_analysis

comment_list = ["I love this product", "I hate this product", "I am not sure about this product"]
labels = ["positive", "negative", "neutral"]
comment_analysis = CommentClassifier(comment_list, 
                                     labels).constitute(subject, verbose=True)

# Print the result
for comment in comment_analysis:
    print(comment["comment"])
    print(comment["analysis"])
    print(comment["selected_label"])
    print("-"*50)