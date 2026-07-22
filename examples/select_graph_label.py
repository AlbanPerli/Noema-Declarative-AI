import _bootstrap
from Noema import *
from _config import (
    env_context_size,
    env_fast_exit,
    env_n_gpu_layers,
    env_suppress_startup_logs,
    env_verbose,
    model_path,
)


llm = LLM(
    model_path('/Users/al/Documents/IA/Models/LLM/gemma4/gemma-4-E4B-it-Q4_K_M.gguf'),
    context_size=env_context_size(),
    n_gpu_layers=env_n_gpu_layers(),
    suppress_startup_logs=env_suppress_startup_logs(),
    verbose=env_verbose(),
    fast_exit=env_fast_exit(),
    reasoning="off",
)


@Noema(llm)
def compact_label(comment):
    """
    You create compact, stable labels for user comments.
    """
    Information(f"Comment: {comment}")

    graph = SelectGraph("compact-comment-label", separator=" ")
    graph.transition("start", "sentiment", ["positive", "neutral", "negative"])
    graph.transition("sentiment", "intensity", ["weak", "clear", "strong"])
    graph.transition("intensity", "end", ["satisfaction", "friction", "request"])

    result = graph.run(
        "start",
        objective="Choose the best compact label for the current comment.",
    )
    print(graph.to_mermaid())
    return result.text


def main():
    label = compact_label("This llm is very good!")
    print(label)


if __name__ == "__main__":
    main()
