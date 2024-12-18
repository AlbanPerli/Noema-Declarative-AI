from Noema import *

# Create a new Subject
Subject("../Models/EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf", verbose=True)

@Noema
def comment_evaluation(comment):
  """
  You are a specialist of comment analysis.
  You always produce a deep analysis of the comment.
  """
  comment_to_analyse = Information(f"{comment}")
  specialists = ["Psychologist", "Product manager", "Satisfaction manager"]
  analyse_by_specialists = {}
  for specialist in specialists:
    analysis = Sentence(f"Analysing the comment as a {specialist}")
    analyse_by_specialists[specialist] = analysis.value
  
  synthesis = Paragraph("Providing a synthesis of the analysis.")
  return synthesis.value, analyse_by_specialists

synthesis, abs = comment_evaluation("This llm is very good!")

print(synthesis)
print(Subject.shared().noema())