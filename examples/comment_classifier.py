import _bootstrap
from Noema import *
from _config import (
    env_context_size,
    env_enable_monitoring,
    env_fast_exit,
    env_n_gpu_layers,
    env_suppress_startup_logs,
    env_verbose,
    model_path,
)

llm = LLM(
    model_path("EXAONE-3.5-2.4B-Instruct-Q4_K_M.gguf"),
    verbose=env_verbose(),
    context_size=env_context_size(),
    n_gpu_layers=env_n_gpu_layers(),
    enable_monitoring=env_enable_monitoring(),
    suppress_startup_logs=env_suppress_startup_logs(),
    fast_exit=env_fast_exit(),
)


@Noema(llm)
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
  qualify_synthesis = Select("Qualify the synthesis", options=["good", "bad", "neutral"])
  print(f"Synthesis: {synthesis.value} is {qualify_synthesis.value}")
  return synthesis.value, analyse_by_specialists

def main():
  synthesis, abs = comment_evaluation("This llm is very good!")

  print(synthesis)


if __name__ == "__main__":
  main()
