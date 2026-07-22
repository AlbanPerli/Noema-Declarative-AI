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
    model_path("/Users/al/Documents/IA/Models/LLM/LFM2.5-8B-A1B-Q4_K_M.gguf"),
    context_size=env_context_size(),
    n_gpu_layers=env_n_gpu_layers(),
    suppress_startup_logs=env_suppress_startup_logs(),
    verbose=env_verbose(),
    fast_exit=env_fast_exit(),
    reasoning="off",
)


@Noema(llm)
def hypothesis_score(hypothesis):
    """
    You evaluate how well an incident hypothesis is supported by the available
    evidence. 0 means unsupported, 10 means strongly supported.
    """
    hypothesis_to_evaluate = Information(f"{hypothesis}")
    score = Float("Score the hypothesis support, between 0 and 10.")
    return score.value


@Noema(llm)
def hypothesis_risk_note(score):
    """
    You explain what a hypothesis score implies for operational risk.
    """
    score_to_explain = Information(f"{score}")
    note = Sentence("Explain the operational risk implied by this score.")
    return note.value


@Noema(llm)
def incident_diagnosis(report):
    """
    You are an incident lead.
    You compare expert hypotheses and converge toward a root-cause conclusion.
    """
    incident_report = Information(f"{report}")
    specialists = ["SRE", "Security engineer", "Backend engineer"]
    hypotheses = {}

    for specialist in specialists:
        hypothesis = Sentence(f"Formulate a causal hypothesis as a {specialist}.")
        hypotheses[specialist] = hypothesis.value
        score = hypothesis_score(hypothesis.value)
        risk_note = hypothesis_risk_note(score)
        checks = ListOf(Sentence, "List three concrete checks for this hypothesis.")

    synthesis = Paragraph("Synthesize the strongest hypothesis and the decisive evidence.")
    root_cause = Substring(f"Extract the root cause from this synthesis: {synthesis.value}")
    print(root_cause.value)
    return synthesis.value


def main():
    synthesis = incident_diagnosis(
        """
        Nightly invoice export failed for every tenant at 02:05. The scheduler
        started normally, payment-api returned 401 invalid_client after a
        credential rotation, and retry succeeds after refreshing the token.
        """
    )
    print(synthesis)


if __name__ == "__main__":
    main()
