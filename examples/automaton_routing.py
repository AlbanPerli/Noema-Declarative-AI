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
def route_incident(report):
    """
    You classify an operational incident and route it to the right handling path.
    Produce concise, non-repetitive outputs.
    """
    graph = Automaton("incident-routing")

    @graph.state("classify")
    def classify():
        Information(f"Incident report: {report}")
        severity = Select(
            "Classify the incident severity.",
            options=["low", "medium", "high"],
        )
        domain = Select(
            "Classify the most likely failing domain.",
            options=["auth", "queue", "scheduler", "dependency"],
        )
        return {"severity": severity, "domain": domain}

    @graph.state("mitigate")
    def mitigate(context):
        domain = context["classify"]["domain"].value
        return Paragraph(f"Draft an immediate mitigation for a {domain} incident.")

    @graph.state("investigate")
    def investigate():
        return Sentence("Extract the next diagnostic question to reduce uncertainty.")

    graph.transition(
        "classify",
        "mitigate",
        when=lambda context: context["classify"]["severity"] == "high",
    )
    graph.transition("classify", "investigate", default=True)

    result = graph.run("classify")
    print(graph.to_mermaid())
    return result.path


def main():
    path = route_incident(
        "Invoice export failed for all tenants after a credential rotation; "
        "payment-api returns 401 invalid_client and the queue is growing."
    )
    print(path)


if __name__ == "__main__":
    main()
