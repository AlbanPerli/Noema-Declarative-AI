import _bootstrap
from Noema import *
from _config import create_subject, run_example

@Noema
def analysis_evaluation(analysis):
    """
    You are a specialist of analysis evaluation.
    You produce a numerical evaluation of the analysis, 0 is bad, 10 is good.
    Good means that the analysis is relevant and useful.
    Bad means that the analysis is not relevant and not useful.
    """
    analysis_to_evaluate = Information(f"{analysis}")
    evaluation = Float("Evaluation of the analysis, between 0 and 10")
    return evaluation.value

@Noema
def comment_note_evaluation(analysis):
    """
    You are a specialist of evaluation commenting.
    You always produce a deep analysis of the comment.
    """
    analysis_to_evaluate = Information(f"{analysis}")
    comment = Sentence("Commenting the analysis")
    return comment.value

@Noema
def comment_evaluation(comment):
  """
  You are a specialist of comment analysis.
  You always produce a deep analysis of the comment.
  """
  comment_to_analyse = Information(f"{comment}")
  specialists = ["Psychologist", "Sociologist", "Linguist", "Philosopher"]
  analyse_by_specialists = {}
  for specialist in specialists:
    analysis = Sentence(f"Analysing the comment as a {specialist}")
    analyse_by_specialists[specialist] = analysis.value
    evaluation = analysis_evaluation(analysis.value)
    comment_note_evaluation_res = comment_note_evaluation(evaluation)
    improvements = ListOf(Sentence, "List 4 improvements")
  
  synthesis = Paragraph("Providing a synthesis of the analysis.")
  sub = Substring(f"Extracting synthesis comment from {synthesis.value}")
  print(sub.value)
  return synthesis.value

def main():
    # Create a new Subject
    create_subject("granite-3.1-3b-a800m-instruct-Q4_K_M.gguf", write_graph=True)
    synthesis = comment_evaluation("This llm is very good!")
    print(synthesis)


run_example(main)
