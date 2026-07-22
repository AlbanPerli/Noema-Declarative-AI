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
    model_path("/Users/al/Documents/IA/Models/LLM/gemma4/gemma-4-E4B-it-Q4_K_M.gguf"),
    context_size=env_context_size("32000"),
    n_gpu_layers=env_n_gpu_layers(),
    suppress_startup_logs=env_suppress_startup_logs(),
    verbose=env_verbose(),
    fast_exit=env_fast_exit(),
    reasoning="off",
)


class EvidenceNotebook(NoemaEnvironment):
    """Stores observed facts and constraints gathered during an investigation."""

    facts = Memory(default_factory=list)
    constraints = Memory(default_factory=list)

    @tool
    def record_fact(self, source: str, observation: str):
        fact = {
            "source": source,
            "observation": observation,
        }
        self.facts.append(fact)
        return {
            "fact": fact,
            "fact_count": len(self.facts),
        }

    @tool
    def record_constraint(self, name: str, value: str):
        constraint = {
            "name": name,
            "value": value,
        }
        self.constraints.append(constraint)
        return constraint

    @tool
    def snapshot(self):
        return {
            "facts": self.facts,
            "constraints": self.constraints,
        }


class HypothesisLab(NoemaEnvironment):
    """Maintains competing explanations and tests them against observations."""

    hypotheses = Memory(default_factory=dict)
    tests = Memory(default_factory=list)
    rejected = Memory(default_factory=list)

    @tool
    def propose_hypothesis(self, name: str, mechanism: str):
        hypothesis = {
            "mechanism": mechanism,
            "score": 0,
            "status": "open",
        }
        self.hypotheses[name] = hypothesis
        return {
            "name": name,
            **hypothesis,
        }

    @tool
    def test_hypothesis(self, name: str, evidence: str, verdict: str):
        normalized = verdict.lower()
        if "support" in normalized or "confirm" in normalized:
            delta = 1
            status = "supported"
        elif "weaken" in normalized or "reject" in normalized or "contradict" in normalized:
            delta = -1
            status = "weakened"
        else:
            delta = 0
            status = "neutral"

        hypothesis = self.hypotheses.setdefault(
            name,
            {"mechanism": "created during testing", "score": 0, "status": "open"},
        )
        hypothesis["score"] += delta
        hypothesis["status"] = status
        test = {
            "hypothesis": name,
            "evidence": evidence,
            "verdict": status,
            "score": hypothesis["score"],
        }
        self.tests.append(test)
        return test

    @tool
    def reject_hypothesis(self, name: str, reason: str):
        hypothesis = self.hypotheses.setdefault(
            name,
            {"mechanism": "created during rejection", "score": 0, "status": "open"},
        )
        hypothesis["status"] = "rejected"
        rejection = {
            "hypothesis": name,
            "reason": reason,
        }
        self.rejected.append(rejection)
        return rejection

    @tool
    def rank_hypotheses(self):
        ranked = sorted(
            (
                {"name": name, **hypothesis}
                for name, hypothesis in self.hypotheses.items()
                if hypothesis["status"] != "rejected"
            ),
            key=lambda hypothesis: hypothesis["score"],
            reverse=True,
        )
        return ranked


class DiagnosticConsole(NoemaEnvironment):
    """Runs small deterministic checks that the LLM can use as evidence."""

    checks = Memory(default_factory=list)

    @tool
    def compare_metric(self, name: str, baseline: float, observed: float):
        if baseline == 0:
            ratio = None
            change_percent = None
        else:
            ratio = observed / baseline
            change_percent = ((observed - baseline) / baseline) * 100

        result = {
            "metric": name,
            "baseline": baseline,
            "observed": observed,
            "ratio": ratio,
            "change_percent": change_percent,
        }
        self.checks.append(result)
        return result

    @tool
    def check_log_contains(self, log_line: str, expected: str):
        found = expected.lower() in log_line.lower()
        result = {
            "log_line": log_line,
            "expected": expected,
            "found": found,
        }
        self.checks.append(result)
        return result


class ResolutionBoard(NoemaEnvironment):
    """Stores the final diagnosis and the operational follow-up."""

    conclusions = Memory(default_factory=list)
    actions = Memory(default_factory=list)

    @tool
    def draw_conclusion(self, root_cause: str, confidence: str, supporting_evidence: str):
        conclusion = {
            "root_cause": root_cause,
            "confidence": confidence,
            "supporting_evidence": supporting_evidence,
        }
        self.conclusions.append(conclusion)
        return conclusion

    @tool
    def plan_action(self, owner: str, action: str, urgency: str):
        next_action = {
            "owner": owner,
            "action": action,
            "urgency": urgency,
        }
        self.actions.append(next_action)
        return next_action

    @tool
    def snapshot(self):
        return {
            "conclusions": self.conclusions,
            "actions": self.actions,
        }


class IncidentInvestigator(NoemaEnvironment):
    """Composes domain objects that help an LLM solve an operational incident."""

    evidence = Component(EvidenceNotebook, description="Collect the facts that constrain the investigation.")
    lab = Component(HypothesisLab, description="Create, test, rank, and reject explanations.")
    console = Component(DiagnosticConsole, description="Run deterministic checks on metrics and logs.")
    resolution = Component(ResolutionBoard, description="Record the final cause and the next action.")

    incident = Visible("nightly invoice export failure")
    goal = Visible("identify the most likely root cause and immediate correction")

    @visible
    @property
    def progress(self):
        return {
            "facts": len(self.evidence.facts),
            "hypotheses": len(self.lab.hypotheses),
            "tests": len(self.lab.tests),
            "rejections": len(self.lab.rejected),
            "checks": len(self.console.checks),
            "conclusions": len(self.resolution.conclusions),
            "actions": len(self.resolution.actions),
        }


def main():
    investigator = IncidentInvestigator(llm=llm)
    incident_notes = """
    - Nightly invoice export failed for every tenant at 02:05.
    - The scheduler started the export job normally.
    - The processing queue grew from 120 to 7800 jobs in 30 minutes.
    - The first failing downstream log says: payment-api 401 invalid_client.
    - A service credential was rotated at 01:50.
    - Manual retry succeeds after refreshing the payment-api token.
    """

    answer = investigator(
        f"""
        Investigate the incident from the notes below.
        Use the component tools to record relevant facts, formulate competing
        hypotheses, run deterministic checks, test the hypotheses, reject the
        weaker explanation, draw a conclusion, and plan the immediate action.
        Choose final only after the investigation has enough recorded evidence.

        Incident notes:
        {incident_notes}
        """,
        max_steps=16,
        max_tokens=160,
    )

    print(answer)
    print(investigator.progress)
    print(investigator.evidence.snapshot())
    print(investigator.lab.rank_hypotheses())
    print(investigator.resolution.snapshot())


if __name__ == "__main__":
    main()
