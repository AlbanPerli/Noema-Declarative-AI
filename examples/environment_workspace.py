import _bootstrap
from Noema import *
from _config import model_path


llm = LLM(
    model_path("/Users/al/Documents/IA/Models/LLM/gemma4/gemma-4-E4B-it-Q4_K_M.gguf"),
)


class FeedbackAnalyzer(NoemaEnvironment):
    """Extracts actionable product signals from raw user feedback."""

    product_area = Visible("local LLM orchestration and developer experience")

    @tool
    def extract_signals(self, comment: str):
        text = comment.lower()
        positive_terms = ["good", "great", "fast", "useful", "powerful", "love"]
        negative_terms = ["bad", "slow", "crash", "broken", "confusing", "wrong"]
        request_terms = ["could", "should", "need", "want", "missing", "add"]

        positive_score = sum(term in text for term in positive_terms)
        negative_score = sum(term in text for term in negative_terms)
        request_score = sum(term in text for term in request_terms)

        if positive_score > negative_score:
            sentiment = "positive"
        elif negative_score > positive_score:
            sentiment = "negative"
        else:
            sentiment = "neutral"

        if negative_score:
            intent = "risk"
        elif request_score:
            intent = "feature_request"
        else:
            intent = "validation"

        intensity = "strong" if max(positive_score, negative_score, request_score) >= 2 else "clear"
        return {
            "sentiment": sentiment,
            "intent": intent,
            "intensity": intensity,
            "evidence": comment,
            "matched_terms": {
                "positive": [term for term in positive_terms if term in text],
                "negative": [term for term in negative_terms if term in text],
                "request": [term for term in request_terms if term in text],
            },
        }

    @tool
    def estimate_impact(self, sentiment: str, intent: str, intensity: str):
        base = {"validation": 2, "feature_request": 3, "risk": 4}.get(intent, 2)
        if intensity == "strong":
            base += 1
        if sentiment == "negative":
            base += 1
        score = min(base, 5)
        return {
            "score": score,
            "priority": "high" if score >= 4 else "medium" if score == 3 else "low",
            "reason": f"{intent} signal with {intensity} intensity and {sentiment} sentiment",
        }


class ProductDecisionBoard(NoemaEnvironment):
    """Keeps structured product decisions produced during the LLM run."""

    insights = Memory(default_factory=list)
    opportunities = Memory(default_factory=list)
    risks = Memory(default_factory=list)

    @tool
    def record_insight(self, title: str, evidence: str, sentiment: str, priority: str):
        insight = {
            "title": title,
            "evidence": evidence,
            "sentiment": sentiment,
            "priority": priority,
        }
        self.insights.append(insight)
        return insight

    @tool
    def open_opportunity(self, title: str, hypothesis: str, expected_user_value: str):
        opportunity = {
            "title": title,
            "hypothesis": hypothesis,
            "expected_user_value": expected_user_value,
            "status": "open",
        }
        self.opportunities.append(opportunity)
        return opportunity

    @tool
    def register_risk(self, title: str, mitigation: str, severity: str):
        risk = {
            "title": title,
            "mitigation": mitigation,
            "severity": severity,
        }
        self.risks.append(risk)
        return risk

    @tool
    def board_snapshot(self):
        return {
            "insights": self.insights,
            "opportunities": self.opportunities,
            "risks": self.risks,
        }


class ExperimentPlanner(NoemaEnvironment):
    """Turns an opportunity into an executable product experiment."""

    experiments = Memory(default_factory=list)

    @tool
    def design_experiment(self, hypothesis: str, metric: str, rollout: str):
        experiment = {
            "hypothesis": hypothesis,
            "metric": metric,
            "rollout": rollout,
            "decision_rule": f"Ship if {metric} improves without regressions during {rollout}.",
        }
        self.experiments.append(experiment)
        return experiment

    @tool
    def propose_validation_questions(self, audience: str, count: int):
        questions = [
            f"What made this experience valuable for {audience}?",
            f"What would make the workflow more reliable for {audience}?",
            f"Which missing control would {audience} expect next?",
            f"What would prevent {audience} from adopting this feature?",
        ]
        return questions[:max(1, min(int(count), len(questions)))]


class FollowUpRouter(NoemaEnvironment):
    """Routes follow-up work to the right team based on the selected signal."""

    routes = Memory(default_factory=list)

    @tool
    def route(self, signal_type: str, priority: str, rationale: str):
        owners = {
            "validation": "product",
            "feature_request": "design+engineering",
            "risk": "engineering",
        }
        route = {
            "owner": owners.get(signal_type, "product"),
            "priority": priority,
            "rationale": rationale,
        }
        self.routes.append(route)
        return route


class ProductFeedbackWorkshop(NoemaEnvironment):
    analyzer = Component(FeedbackAnalyzer, description="Find sentiment, intent, and impact.")
    board = Component(ProductDecisionBoard, description="Persist product decisions from the run.")
    planner = Component(ExperimentPlanner, description="Turn decisions into testable experiments.")
    router = Component(FollowUpRouter, description="Assign concrete follow-up ownership.")

    product = Visible("Noema declarative local-LLM programming interface")
    objective = Visible("turn qualitative comments into product decisions")

    @visible
    @property
    def open_decisions(self):
        return {
            "insights": len(self.board.insights),
            "opportunities": len(self.board.opportunities),
            "risks": len(self.board.risks),
            "experiments": len(self.planner.experiments),
            "routes": len(self.router.routes),
        }


def main():
    workshop = ProductFeedbackWorkshop(llm=llm)
    comment = (
        "Noema's object composition feels powerful. "
        "I want a clearer way to see which object acted and why."
    )

    answer = workshop(
        f"""
        Triage this product feedback for the Noema roadmap.
        Use the available component tools to extract signals, estimate impact,
        record a product insight, open an opportunity or risk if useful,
        design one validation experiment, route the follow-up, then finish
        with a concise product decision.

        Feedback: {comment}
        """,
        max_steps=8,
        max_tokens=120,
    )
    print(answer)

    print(workshop.open_decisions)
    print(workshop.board.board_snapshot())
    print(workshop.planner.experiments)
    print(workshop.router.routes)


if __name__ == "__main__":
    main()
