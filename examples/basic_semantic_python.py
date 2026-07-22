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
    model_path("/Users/al/Documents/IA/Models/LLM/LFM2.5-8B-A1B-Q4_K_M.gguf"),
    verbose=env_verbose(),
    context_size=env_context_size(),
    n_gpu_layers=env_n_gpu_layers(),
    enable_monitoring=env_enable_monitoring(),
    suppress_startup_logs=env_suppress_startup_logs(),
    fast_exit=env_fast_exit(),
)


@Noema(llm)
def simple_task(task, parameters):
    """You are an incredible Python developer.
    Always looking for the best way to write code."""
    task_to_code = Information(f"I want to {task}")
    reformulation = Sentence("Reformulate the task to be easily understood by a Python developer.")
    decomposition = ListOf(Sentence,"Decompose the task into smaller sub-tasks.")
    result = SemPy(reformulation.value)(parameters) 
    return result.value
    
def main():
    nb_letter = simple_task("Count the occurence of letters in a word", "strawberry")
    print(nb_letter)


if __name__ == "__main__":
    main()
