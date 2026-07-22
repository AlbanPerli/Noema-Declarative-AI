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
    model_path("gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"),
    context_size=env_context_size(),
    n_gpu_layers=env_n_gpu_layers(),
    suppress_startup_logs=env_suppress_startup_logs(),
    verbose=env_verbose(),
    fast_exit=env_fast_exit(),
    reasoning="off",
)


@Noema(llm)
def route_comment(comment):
    """
    You classify a user comment and route it to the right handling path.
    Produce concise, non-repetitive outputs.
    """
    graph = Automaton("comment-routing")

    @graph.state("classify")
    def classify():
        Information(f"Comment: {comment}")
        sentiment = Select(
            "Classify the sentiment.",
            options=["positive", "neutral", "negative"],
        )
        intent = Select(
            "Classify the intent.",
            options=["praise", "bug_report", "feature_request", "complaint"],
        )
        return {"sentiment": sentiment, "intent": intent}

    @graph.state("support")
    def support(context):
        intent = context["classify"]["intent"].value
        reply = Paragraph(f"Draft a short support response for this intent: {intent}.")
        return reply

    @graph.state("product")
    def product():
        insight = Sentence("Extract the main product insight from the comment.")
        return insight

    graph.transition(
        "classify",
        "support",
        when=lambda context: context["classify"]["intent"].in_(["bug_report", "complaint"]),
    )
    graph.transition("classify", "product", default=True)

    result = graph.run("classify")
    print(graph.to_mermaid())
    return result.path


def main():
    path = route_comment("This llm is very good!")
    print(path)


if __name__ == "__main__":
    main()
