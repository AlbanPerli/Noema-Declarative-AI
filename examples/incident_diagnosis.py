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
    model_path("/Users/al/Documents/IA/Models/LLM/gemma4/gemma-4-26B-A4B-it-UD-Q4_K_M.gguf"),
    context_size=env_context_size(),
    n_gpu_layers=env_n_gpu_layers(),
    suppress_startup_logs=env_suppress_startup_logs(),
    verbose=env_verbose(),
    fast_exit=env_fast_exit(),
    reasoning="off",
)


@Noema(llm)
def diagnose_incident(report):
    """
    You are a pragmatic incident diagnostician.
    You reason from observed facts, compare competing hypotheses, and conclude
    with the most likely cause and the next corrective action.
    """
    incident_report = Information(f"{report}")
    observations = ListOf(Sentence, "Extract three factual observations from the incident report.")
    primary_hypothesis = Sentence("State the most likely causal hypothesis.")
    alternative_hypothesis = Sentence("State one plausible alternative hypothesis.")
    decisive_evidence = Sentence(
        f"Identify the observation that best discriminates between {primary_hypothesis.value} "
        f"and {alternative_hypothesis.value}."
    )
    conclusion = Paragraph(
        "Conclude with the likely root cause and one immediate corrective action."
    )
    urgency = Select("Classify the operational urgency.", options=["low", "medium", "high"])
    print(f"Urgency: {urgency.value}")
    return {
        "observations": observations.value,
        "primary_hypothesis": primary_hypothesis.value,
        "alternative_hypothesis": alternative_hypothesis.value,
        "decisive_evidence": decisive_evidence.value,
        "conclusion": conclusion.value,
        "urgency": urgency.value,
    }


def main():
    diagnosis = diagnose_incident(
        """
        Nightly invoice export failed for every tenant at 02:05.
        The scheduler started normally, but payment-api returned 401 invalid_client
        immediately after a service credential rotation. The queue grew from
        120 to 7800 jobs, and manual retry succeeds after refreshing the token.
        """
    )
    print(diagnosis["conclusion"])


if __name__ == "__main__":
    main()
