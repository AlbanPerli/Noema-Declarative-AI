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
def compact_incident_label(report):
    """
    You create compact, stable labels for operational incidents.
    """
    Information(f"Incident report: {report}")

    graph = SelectGraph("compact-incident-label", separator=" ")
    graph.transition("start", "domain", ["auth", "queue", "scheduler", "dependency"])
    graph.transition("domain", "impact", ["single-tenant", "multi-tenant", "global"])
    graph.transition("impact", "action", ["refresh-token", "scale-workers", "rollback", "investigate"])

    result = graph.run(
        "start",
        objective="Choose the best compact incident label for the current report.",
    )
    print(graph.to_mermaid())
    return result.text


def main():
    label = compact_incident_label(
        "Invoice export failed for all tenants after a credential rotation; "
        "payment-api returns 401 invalid_client."
    )
    print(label)


if __name__ == "__main__":
    main()
