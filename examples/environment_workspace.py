from __future__ import annotations

import json
import math
import re
import statistics
from dataclasses import dataclass, field
from typing import Any, Iterable

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


# ============================================================
# Configuration
# ============================================================

MODEL_DIRECTORY = "/Users/al/Documents/IA/Models/LLM"

GENERATOR_MODELS = [
    f"{MODEL_DIRECTORY}/gemma4/gemma-4-E4B-it-Q4_K_M.gguf",
    f"{MODEL_DIRECTORY}/gemma4/gemma-4-12b-it-Q4_K_M.gguf",
]

CRITIC_MODELS = [
    f"{MODEL_DIRECTORY}/gemma4/gemma-4-12b-it-Q4_K_M.gguf",
    f"{MODEL_DIRECTORY}/Qwen3.6-27B-Q4_K_M.gguf",
]

VERIFIER_MODELS = [
    f"{MODEL_DIRECTORY}/gemma4/gemma-4-E4B-it-Q4_K_M.gguf",
]

JUDGE_MODELS = [
    f"{MODEL_DIRECTORY}/Qwen3.6-27B-Q4_K_M.gguf",
]

MAX_ITERATIONS = 4
MINIMUM_ACCEPTED_SCORE = 8.2
MAXIMUM_CRITICAL_ISSUES = 0
MINIMUM_SCORE_GAIN = 0.15

ROLE_MAX_STEPS = 8
ROLE_MAX_TOKENS = 1400


# ============================================================
# Construction des LLM
# ============================================================

def build_llm(path: str) -> LLM:
    return LLM(
        model_path(path),
        context_size=env_context_size("64000"),
        n_gpu_layers=env_n_gpu_layers(),
        suppress_startup_logs=env_suppress_startup_logs(),
        verbose=env_verbose(),
        fast_exit=env_fast_exit(),
        reasoning="off",
    )


generator_llms = [build_llm(path) for path in GENERATOR_MODELS]
critic_llms = [build_llm(path) for path in CRITIC_MODELS]
verifier_llms = [build_llm(path) for path in VERIFIER_MODELS]
judge_llms = [build_llm(path) for path in JUDGE_MODELS]


# ============================================================
# Utilitaires généraux
# ============================================================

def clamp(value: float, minimum: float, maximum: float) -> float:
    return max(minimum, min(maximum, value))


def mean(values: Iterable[float], default: float = 0.0) -> float:
    items = list(values)
    return statistics.mean(items) if items else default


def median(values: Iterable[float], default: float = 0.0) -> float:
    items = list(values)
    return statistics.median(items) if items else default


def normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text.strip().lower())


def lexical_similarity(left: str, right: str) -> float:
    """
    Mesure simple de similarité Jaccard.

    Elle sert seulement à détecter des réponses presque identiques.
    Elle ne remplace pas une mesure sémantique.
    """
    left_tokens = set(re.findall(r"\w+", normalize_text(left)))
    right_tokens = set(re.findall(r"\w+", normalize_text(right)))

    if not left_tokens and not right_tokens:
        return 1.0

    if not left_tokens or not right_tokens:
        return 0.0

    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)

    return intersection / union if union else 0.0


def extract_json_object(text: str) -> dict[str, Any]:
    """
    Extrait le premier objet JSON valide d'une réponse.

    Le modèle est invité à utiliser un outil structuré, mais cette fonction
    constitue une défense supplémentaire contre les sorties imparfaites.
    """
    text = text.strip()

    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()

    for index, character in enumerate(text):
        if character != "{":
            continue

        try:
            parsed, _ = decoder.raw_decode(text[index:])
            if isinstance(parsed, dict):
                return parsed
        except json.JSONDecodeError:
            continue

    raise ValueError(f"Aucun objet JSON valide trouvé dans la sortie :\n{text}")


def safe_json_dumps(value: Any) -> str:
    return json.dumps(
        value,
        ensure_ascii=False,
        indent=2,
        default=str,
    )


def contains_placeholder(value: Any) -> bool:
    if value is Ellipsis:
        return True

    if isinstance(value, str):
        normalized = value.strip().lower()
        return normalized in {"...", "…", "todo", "tbd", "placeholder", "à compléter"}

    if isinstance(value, dict):
        return any(contains_placeholder(item) for item in value.values())

    if isinstance(value, (list, tuple, set)):
        return any(contains_placeholder(item) for item in value)

    return False


# ============================================================
# Environnement générique d'un rôle
# ============================================================

class StructuredRole(NoemaEnvironment):
    """
    Un rôle LLM indépendant.

    Chaque instance dispose de son propre modèle, de son propre contexte
    et d'une mémoire séparée.
    """

    role_name = Visible("unassigned")
    role_goal = Visible("produce a structured result")

    submissions = Memory(default_factory=list)

    @tool(
        description=(
            "Submit the role result. The payload argument must be a JSON object "
            "that conforms to the requested schema."
        )
    )
    def submit_result(self, payload: dict):
        if not isinstance(payload, dict):
            return {
                "error": {
                    "type": "invalid_payload",
                    "message": "submit_result payload must be a JSON object.",
                    "received_type": type(payload).__name__,
                    "hint": "Call submit_result again with payload set to the complete result object.",
                }
            }

        if contains_placeholder(payload):
            return {
                "error": {
                    "type": "placeholder_payload",
                    "message": "submit_result payload still contains placeholders.",
                    "hint": "Replace every placeholder with concrete task-specific content.",
                }
            }

        record = {
            "role": self.role_name,
            "payload": payload,
        }

        self.submissions.append(record)
        return record

    @tool(description="Return the latest submitted structured result.")
    def latest_result(self):
        if not self.submissions:
            return None

        return self.submissions[-1]

    def run_structured(
        self,
        instructions: str,
        expected_schema: dict[str, Any],
        max_steps: int = ROLE_MAX_STEPS,
        max_tokens: int = ROLE_MAX_TOKENS,
    ) -> dict[str, Any]:
        """
        Appelle le rôle et récupère son résultat structuré.
        """
        self.submissions.clear()

        raw_answer = self(
            f"""
            You are acting as: {self.role_name}

            Your role objective:
            {self.role_goal}

            Task:
            {instructions}

            Required JSON structure:
            {safe_json_dumps(expected_schema)}

            Rules:
            - Work independently.
            - Do not assume another model has checked your work.
            - Identify uncertainty explicitly.
            - Do not expose hidden chain-of-thought.
            - Give concise conclusions and observable justifications only.
            - Call submit_result exactly once with this argument shape:
              {{"payload": <object matching the Required JSON structure>}}
            - Do not use placeholders such as "...", "TODO", or "TBD".
            - Do not call final before submit_result.
            """,
            max_steps=max_steps,
            max_tokens=max_tokens,
        )

        latest = self.latest_result()

        if latest and isinstance(latest.get("payload"), dict):
            return latest["payload"]

        return extract_json_object(str(raw_answer))


# ============================================================
# Générateurs
# ============================================================

class CandidateGenerator(StructuredRole):
    role_name = Visible("candidate_generator")
    role_goal = Visible(
        "Produce a strong candidate answer without evaluating other candidates."
    )


class AlternativeGenerator(StructuredRole):
    role_name = Visible("alternative_generator")
    role_goal = Visible(
        "Produce a substantially different candidate using another decomposition."
    )


# ============================================================
# Critiques spécialisés
# ============================================================

class CorrectnessCritic(StructuredRole):
    role_name = Visible("correctness_critic")
    role_goal = Visible(
        "Find factual, logical, causal, technical, and inferential errors."
    )


class CompletenessCritic(StructuredRole):
    role_name = Visible("completeness_critic")
    role_goal = Visible(
        "Find omitted requirements, missing cases, and incomplete explanations."
    )


class ClarityCritic(StructuredRole):
    role_name = Visible("clarity_critic")
    role_goal = Visible(
        "Evaluate clarity, structure, precision, readability, and ambiguity."
    )


class AssumptionCritic(StructuredRole):
    role_name = Visible("assumption_critic")
    role_goal = Visible(
        "Expose unsupported assumptions, hidden premises, and unjustified confidence."
    )


class AdversarialCritic(StructuredRole):
    role_name = Visible("adversarial_red_team")
    role_goal = Visible(
        "Try to falsify the answer by constructing counterexamples and failure scenarios."
    )


class RequirementCritic(StructuredRole):
    role_name = Visible("requirement_critic")
    role_goal = Visible(
        "Check whether every explicit user requirement is satisfied."
    )


# ============================================================
# Vérificateurs
# ============================================================

class EvidenceVerifier(StructuredRole):
    role_name = Visible("evidence_verifier")
    role_goal = Visible(
        "Check whether claims are supported by the supplied source material."
    )


class ConsistencyVerifier(StructuredRole):
    role_name = Visible("consistency_verifier")
    role_goal = Visible(
        "Detect internal contradictions and conflicts between claims."
    )


class BlindSpotExplorer(StructuredRole):
    role_name = Visible("blind_spot_explorer")
    role_goal = Visible(
        "Search for perspectives, edge cases, alternative mechanisms, and risks "
        "not considered by the candidate or existing critiques."
    )


# ============================================================
# Arbitres
# ============================================================

class CandidateJudge(StructuredRole):
    role_name = Visible("candidate_judge")
    role_goal = Visible(
        "Compare candidates and critiques, then rank candidates without rewriting them."
    )


class SynthesisEditor(StructuredRole):
    role_name = Visible("synthesis_editor")
    role_goal = Visible(
        "Create a revised answer from the strongest candidate and valid critiques."
    )


class FinalAuditor(StructuredRole):
    role_name = Visible("final_auditor")
    role_goal = Visible(
        "Perform a final independent audit and decide whether publication is safe."
    )


# ============================================================
# Structures de données
# ============================================================

@dataclass
class Candidate:
    candidate_id: str
    content: str
    source_role: str
    iteration: int
    strategy: str = ""
    assumptions: list[str] = field(default_factory=list)
    score: float = 0.0


@dataclass
class Critique:
    critic_role: str
    candidate_id: str
    scores: dict[str, float]
    issues: list[dict[str, Any]]
    strengths: list[str]
    recommendation: str
    confidence: float


@dataclass
class DeterministicReport:
    passed: bool
    score: float
    issues: list[dict[str, Any]]
    metrics: dict[str, Any]


@dataclass
class IterationRecord:
    iteration: int
    candidates: list[Candidate]
    critiques: list[Critique]
    deterministic_reports: dict[str, DeterministicReport]
    selected_candidate_id: str | None
    selected_score: float
    decision: str
    reason: str


# ============================================================
# Mémoire globale de l'investigation réflexive
# ============================================================

@dataclass
class ReflectionState:
    user_request: str
    source_material: str
    requirements: list[str]

    iterations: list[IterationRecord] = field(default_factory=list)

    best_candidate: Candidate | None = None
    best_score: float = 0.0

    final_answer: str | None = None
    finish_reason: str | None = None


# ============================================================
# Contrôles déterministes
# ============================================================

def deterministic_checks(
    candidate: Candidate,
    requirements: list[str],
    minimum_length: int = 200,
    maximum_length: int = 8000,
) -> DeterministicReport:
    text = candidate.content.strip()
    normalized = normalize_text(text)

    issues: list[dict[str, Any]] = []
    metrics: dict[str, Any] = {}

    length = len(text)
    metrics["character_count"] = length

    if length < minimum_length:
        issues.append(
            {
                "type": "too_short",
                "severity": "major",
                "description": (
                    f"La réponse contient {length} caractères, "
                    f"en dessous du minimum de {minimum_length}."
                ),
            }
        )

    if length > maximum_length:
        issues.append(
            {
                "type": "too_long",
                "severity": "minor",
                "description": (
                    f"La réponse contient {length} caractères, "
                    f"au-dessus du maximum de {maximum_length}."
                ),
            }
        )

    absolute_markers = [
        "sans aucun doute",
        "garanti",
        "toujours vrai",
        "impossible que",
        "certain à 100",
        "aucun risque",
    ]

    found_absolute_markers = [
        marker
        for marker in absolute_markers
        if marker in normalized
    ]

    metrics["overconfidence_markers"] = found_absolute_markers

    if found_absolute_markers:
        issues.append(
            {
                "type": "overconfidence",
                "severity": "major",
                "description": (
                    "Formulations excessivement certaines : "
                    + ", ".join(found_absolute_markers)
                ),
            }
        )

    suspicious_placeholders = re.findall(
        r"\b(?:todo|tbd|à compléter|xxx|placeholder)\b",
        normalized,
    )

    metrics["placeholders"] = suspicious_placeholders

    if suspicious_placeholders:
        issues.append(
            {
                "type": "unfinished_content",
                "severity": "critical",
                "description": (
                    "La réponse contient des éléments non finalisés : "
                    + ", ".join(sorted(set(suspicious_placeholders)))
                ),
            }
        )

    repeated_sentences = find_repeated_sentences(text)
    metrics["repeated_sentences"] = repeated_sentences

    if repeated_sentences:
        issues.append(
            {
                "type": "repetition",
                "severity": "minor",
                "description": (
                    f"{len(repeated_sentences)} phrase(s) semblent répétées."
                ),
            }
        )

    requirements_coverage = {}
    for requirement in requirements:
        tokens = set(re.findall(r"\w+", normalize_text(requirement)))
        present = sum(token in normalized for token in tokens)
        ratio = present / len(tokens) if tokens else 1.0
        requirements_coverage[requirement] = ratio

    metrics["requirements_lexical_coverage"] = requirements_coverage

    low_coverage = [
        requirement
        for requirement, coverage in requirements_coverage.items()
        if coverage < 0.15
    ]

    if low_coverage:
        issues.append(
            {
                "type": "possible_requirement_omission",
                "severity": "major",
                "description": (
                    "Certaines exigences semblent peu représentées : "
                    + "; ".join(low_coverage)
                ),
            }
        )

    severity_penalties = {
        "minor": 0.35,
        "major": 1.0,
        "critical": 2.5,
    }

    penalty = sum(
        severity_penalties.get(issue["severity"], 0.5)
        for issue in issues
    )

    score = clamp(10.0 - penalty, 0.0, 10.0)

    critical_issues = sum(
        issue["severity"] == "critical"
        for issue in issues
    )

    passed = (
        critical_issues == 0
        and score >= 7.5
        and not low_coverage
    )

    return DeterministicReport(
        passed=passed,
        score=score,
        issues=issues,
        metrics=metrics,
    )


def find_repeated_sentences(text: str) -> list[str]:
    sentences = [
        normalize_text(sentence)
        for sentence in re.split(r"(?<=[.!?])\s+", text)
        if len(normalize_text(sentence)) >= 30
    ]

    counts: dict[str, int] = {}

    for sentence in sentences:
        counts[sentence] = counts.get(sentence, 0) + 1

    return [
        sentence
        for sentence, count in counts.items()
        if count > 1
    ]


# ============================================================
# Création des agents
# ============================================================

def create_agents():
    generators: list[StructuredRole] = []

    for index, model in enumerate(generator_llms):
        if index % 2 == 0:
            generators.append(CandidateGenerator(llm=model))
        else:
            generators.append(AlternativeGenerator(llm=model))

    critic_classes = [
        CorrectnessCritic,
        CompletenessCritic,
        ClarityCritic,
        AssumptionCritic,
        AdversarialCritic,
        RequirementCritic,
    ]

    critics: list[StructuredRole] = []

    for index, critic_class in enumerate(critic_classes):
        model = critic_llms[index % len(critic_llms)]
        critics.append(critic_class(llm=model))

    verifiers: list[StructuredRole] = []

    verifier_classes = [
        EvidenceVerifier,
        ConsistencyVerifier,
        BlindSpotExplorer,
    ]

    for index, verifier_class in enumerate(verifier_classes):
        model = verifier_llms[index % len(verifier_llms)]
        verifiers.append(verifier_class(llm=model))

    judges = [
        CandidateJudge(llm=model)
        for model in judge_llms
    ]

    editors = [
        SynthesisEditor(llm=model)
        for model in generator_llms
    ]

    auditors = [
        FinalAuditor(llm=model)
        for model in judge_llms
    ]

    return generators, critics, verifiers, judges, editors, auditors


# ============================================================
# Génération
# ============================================================

GENERATOR_SCHEMA = {
    "answer": "string",
    "strategy": "short description of the approach",
    "assumptions": ["explicit assumption"],
    "uncertainties": ["remaining uncertainty"],
}


def generate_initial_candidates(
    generators: list[StructuredRole],
    state: ReflectionState,
    iteration: int,
) -> list[Candidate]:
    candidates: list[Candidate] = []

    existing_answers: list[str] = []

    for index, generator in enumerate(generators):
        diversity_instruction = ""

        if existing_answers:
            diversity_instruction = f"""
            Other candidates already exist.

            Their contents are supplied only to encourage diversity:
            {safe_json_dumps(existing_answers)}

            Use a genuinely different decomposition, ordering, or explanatory
            strategy. Do not merely paraphrase them.
            """

        result = generator.run_structured(
            instructions=f"""
            Produce one complete candidate answer.

            User request:
            {state.user_request}

            Source material:
            {state.source_material}

            Explicit requirements:
            {safe_json_dumps(state.requirements)}

            {diversity_instruction}

            The answer must:
            - respond directly to the user;
            - distinguish observations from assumptions;
            - avoid invented facts;
            - mention meaningful uncertainty;
            - remain self-contained;
            - not mention the multi-agent process.
            """,
            expected_schema=GENERATOR_SCHEMA,
        )

        answer = str(result.get("answer", "")).strip()

        if not answer:
            continue

        candidate = Candidate(
            candidate_id=f"i{iteration}-g{index + 1}",
            content=answer,
            source_role=str(generator.role_name),
            iteration=iteration,
            strategy=str(result.get("strategy", "")),
            assumptions=[
                str(item)
                for item in result.get("assumptions", [])
            ],
        )

        candidates.append(candidate)
        existing_answers.append(answer)

    return deduplicate_candidates(candidates)


def deduplicate_candidates(
    candidates: list[Candidate],
    threshold: float = 0.88,
) -> list[Candidate]:
    unique: list[Candidate] = []

    for candidate in candidates:
        duplicate = any(
            lexical_similarity(candidate.content, other.content) >= threshold
            for other in unique
        )

        if not duplicate:
            unique.append(candidate)

    return unique


# ============================================================
# Critique
# ============================================================

CRITIQUE_SCHEMA = {
    "candidate_id": "string",
    "scores": {
        "correctness": 0,
        "relevance": 0,
        "completeness": 0,
        "clarity": 0,
        "consistency": 0,
        "grounding": 0,
    },
    "strengths": ["specific strength"],
    "issues": [
        {
            "type": "string",
            "severity": "minor|major|critical",
            "description": "specific observable problem",
            "evidence": "excerpt or precise location",
            "correction": "actionable correction",
        }
    ],
    "recommendation": "accept|revise|reject",
    "confidence": 0.0,
}


def critique_candidate(
    critic: StructuredRole,
    candidate: Candidate,
    state: ReflectionState,
) -> Critique:
    result = critic.run_structured(
        instructions=f"""
        Audit this candidate independently.

        User request:
        {state.user_request}

        Source material:
        {state.source_material}

        Explicit requirements:
        {safe_json_dumps(state.requirements)}

        Candidate identifier:
        {candidate.candidate_id}

        Candidate:
        {candidate.content}

        Important:
        - Search actively for errors.
        - Do not reward eloquence when correctness is uncertain.
        - Every issue must point to observable content.
        - Do not invent missing source facts.
        - Use scores from 0 to 10.
        """,
        expected_schema=CRITIQUE_SCHEMA,
    )

    scores = {
        dimension: clamp(float(score), 0.0, 10.0)
        for dimension, score in result.get("scores", {}).items()
        if isinstance(score, (int, float))
    }

    issues = []

    for issue in result.get("issues", []):
        if not isinstance(issue, dict):
            continue

        severity = str(issue.get("severity", "major")).lower()

        if severity not in {"minor", "major", "critical"}:
            severity = "major"

        issues.append(
            {
                **issue,
                "severity": severity,
            }
        )

    return Critique(
        critic_role=str(critic.role_name),
        candidate_id=candidate.candidate_id,
        scores=scores,
        issues=issues,
        strengths=[
            str(item)
            for item in result.get("strengths", [])
        ],
        recommendation=str(
            result.get("recommendation", "revise")
        ).lower(),
        confidence=clamp(
            float(result.get("confidence", 0.5)),
            0.0,
            1.0,
        ),
    )


def run_critiques(
    critics: list[StructuredRole],
    candidates: list[Candidate],
    state: ReflectionState,
) -> list[Critique]:
    all_critiques: list[Critique] = []

    for candidate in candidates:
        for critic in critics:
            try:
                critique = critique_candidate(
                    critic=critic,
                    candidate=candidate,
                    state=state,
                )
                all_critiques.append(critique)
            except Exception as error:
                all_critiques.append(
                    Critique(
                        critic_role=str(critic.role_name),
                        candidate_id=candidate.candidate_id,
                        scores={},
                        issues=[
                            {
                                "type": "critic_failure",
                                "severity": "major",
                                "description": str(error),
                                "correction": (
                                    "Faire vérifier le candidat par un autre critique."
                                ),
                            }
                        ],
                        strengths=[],
                        recommendation="revise",
                        confidence=0.0,
                    )
                )

    return all_critiques


# ============================================================
# Vérification croisée et recherche d'angles morts
# ============================================================

VERIFIER_SCHEMA = {
    "candidate_id": "string",
    "passed": True,
    "score": 0,
    "verified_claims": [
        {
            "claim": "string",
            "status": "supported|unsupported|uncertain|contradicted",
            "basis": "string",
        }
    ],
    "issues": [
        {
            "type": "string",
            "severity": "minor|major|critical",
            "description": "string",
            "correction": "string",
        }
    ],
    "blind_spots": ["missing perspective or case"],
    "confidence": 0.0,
}


def verify_candidate(
    verifier: StructuredRole,
    candidate: Candidate,
    state: ReflectionState,
    critiques: list[Critique],
) -> Critique:
    candidate_critiques = [
        critique
        for critique in critiques
        if critique.candidate_id == candidate.candidate_id
    ]

    result = verifier.run_structured(
        instructions=f"""
        Verify the candidate independently.

        User request:
        {state.user_request}

        Source material:
        {state.source_material}

        Requirements:
        {safe_json_dumps(state.requirements)}

        Candidate:
        {candidate.content}

        Existing critiques:
        {safe_json_dumps([
            {
                "critic": critique.critic_role,
                "issues": critique.issues,
                "scores": critique.scores,
            }
            for critique in candidate_critiques
        ])}

        Do not simply agree with the critiques.
        Check whether each important concern is valid.
        Search for additional blind spots missed by all previous roles.
        """,
        expected_schema=VERIFIER_SCHEMA,
    )

    issues = []

    for issue in result.get("issues", []):
        if not isinstance(issue, dict):
            continue

        severity = str(issue.get("severity", "major")).lower()

        if severity not in {"minor", "major", "critical"}:
            severity = "major"

        issues.append(
            {
                **issue,
                "severity": severity,
            }
        )

    for blind_spot in result.get("blind_spots", []):
        issues.append(
            {
                "type": "blind_spot",
                "severity": "major",
                "description": str(blind_spot),
                "correction": (
                    "Examiner explicitement ce cas dans la prochaine révision."
                ),
            }
        )

    verifier_score = clamp(float(result.get("score", 0.0)), 0.0, 10.0)

    return Critique(
        critic_role=str(verifier.role_name),
        candidate_id=candidate.candidate_id,
        scores={
            "verification": verifier_score,
        },
        issues=issues,
        strengths=[],
        recommendation=(
            "accept"
            if result.get("passed") and not issues
            else "revise"
        ),
        confidence=clamp(
            float(result.get("confidence", 0.5)),
            0.0,
            1.0,
        ),
    )


def run_verifiers(
    verifiers: list[StructuredRole],
    candidates: list[Candidate],
    state: ReflectionState,
    critiques: list[Critique],
) -> list[Critique]:
    reports: list[Critique] = []

    for candidate in candidates:
        for verifier in verifiers:
            reports.append(
                verify_candidate(
                    verifier=verifier,
                    candidate=candidate,
                    state=state,
                    critiques=critiques,
                )
            )

    return reports


# ============================================================
# Calcul du score consolidé
# ============================================================

DIMENSION_WEIGHTS = {
    "correctness": 1.8,
    "relevance": 1.2,
    "completeness": 1.3,
    "clarity": 0.8,
    "consistency": 1.2,
    "grounding": 1.8,
    "verification": 1.8,
}


def aggregate_candidate_score(
    candidate: Candidate,
    critiques: list[Critique],
    deterministic_report: DeterministicReport,
) -> float:
    candidate_critiques = [
        critique
        for critique in critiques
        if critique.candidate_id == candidate.candidate_id
    ]

    weighted_scores: list[float] = []
    weights: list[float] = []

    for critique in candidate_critiques:
        confidence_weight = max(0.25, critique.confidence)

        for dimension, score in critique.scores.items():
            dimension_weight = DIMENSION_WEIGHTS.get(dimension, 1.0)
            weight = confidence_weight * dimension_weight

            weighted_scores.append(score * weight)
            weights.append(weight)

    llm_score = (
        sum(weighted_scores) / sum(weights)
        if weights
        else 0.0
    )

    severity_penalty = 0.0

    for critique in candidate_critiques:
        for issue in critique.issues:
            severity = issue.get("severity", "major")

            if severity == "critical":
                severity_penalty += 1.25
            elif severity == "major":
                severity_penalty += 0.35
            else:
                severity_penalty += 0.08

    combined = (
        0.75 * llm_score
        + 0.25 * deterministic_report.score
        - severity_penalty
    )

    return round(clamp(combined, 0.0, 10.0), 3)


def count_issues(
    candidate_id: str,
    critiques: list[Critique],
    severity: str,
) -> int:
    return sum(
        issue.get("severity") == severity
        for critique in critiques
        if critique.candidate_id == candidate_id
        for issue in critique.issues
    )


# ============================================================
# Arbitrage
# ============================================================

JUDGE_SCHEMA = {
    "ranking": [
        {
            "candidate_id": "string",
            "rank": 1,
            "score": 0,
            "reason": "brief evidence-based reason",
        }
    ],
    "selected_candidate_id": "string",
    "selection_confidence": 0.0,
    "unresolved_risks": ["string"],
}


def judge_candidates(
    judges: list[StructuredRole],
    candidates: list[Candidate],
    critiques: list[Critique],
    deterministic_reports: dict[str, DeterministicReport],
    state: ReflectionState,
) -> tuple[str | None, dict[str, Any]]:
    if not candidates:
        return None, {
            "reason": "Aucun candidat disponible.",
        }

    judge_votes: list[dict[str, Any]] = []

    compact_candidates = [
        {
            "candidate_id": candidate.candidate_id,
            "content": candidate.content,
            "computed_score": candidate.score,
            "deterministic": {
                "passed": deterministic_reports[candidate.candidate_id].passed,
                "score": deterministic_reports[candidate.candidate_id].score,
                "issues": deterministic_reports[candidate.candidate_id].issues,
            },
            "critiques": [
                {
                    "critic": critique.critic_role,
                    "scores": critique.scores,
                    "issues": critique.issues,
                    "recommendation": critique.recommendation,
                    "confidence": critique.confidence,
                }
                for critique in critiques
                if critique.candidate_id == candidate.candidate_id
            ],
        }
        for candidate in candidates
    ]

    for judge in judges:
        result = judge.run_structured(
            instructions=f"""
            Rank the candidates.

            User request:
            {state.user_request}

            Source material:
            {state.source_material}

            Requirements:
            {safe_json_dumps(state.requirements)}

            Candidates and audits:
            {safe_json_dumps(compact_candidates)}

            Selection rules:
            - Correctness and grounding dominate style.
            - A critical unresolved issue should normally disqualify a candidate.
            - Do not choose a candidate solely because its prose is polished.
            - Prefer the candidate with the best robust score across critics.
            """,
            expected_schema=JUDGE_SCHEMA,
        )

        judge_votes.append(result)

    vote_counts: dict[str, int] = {}
    confidence_sums: dict[str, float] = {}

    for vote in judge_votes:
        candidate_id = str(vote.get("selected_candidate_id", ""))

        if not candidate_id:
            continue

        vote_counts[candidate_id] = vote_counts.get(candidate_id, 0) + 1
        confidence_sums[candidate_id] = (
            confidence_sums.get(candidate_id, 0.0)
            + clamp(float(vote.get("selection_confidence", 0.5)), 0.0, 1.0)
        )

    if not vote_counts:
        selected = max(candidates, key=lambda item: item.score)

        return selected.candidate_id, {
            "method": "computed_score_fallback",
            "judge_votes": judge_votes,
        }

    selected_id = max(
        vote_counts,
        key=lambda candidate_id: (
            vote_counts[candidate_id],
            confidence_sums.get(candidate_id, 0.0),
            next(
                (
                    candidate.score
                    for candidate in candidates
                    if candidate.candidate_id == candidate_id
                ),
                0.0,
            ),
        ),
    )

    return selected_id, {
        "method": "judge_consensus",
        "vote_counts": vote_counts,
        "confidence_sums": confidence_sums,
        "judge_votes": judge_votes,
    }


# ============================================================
# Révision
# ============================================================

REVISION_SCHEMA = {
    "answer": "complete revised answer",
    "changes": ["specific correction made"],
    "rejected_feedback": [
        {
            "feedback": "string",
            "reason": "why it was not applied",
        }
    ],
    "remaining_uncertainties": ["string"],
}


def build_revision_candidates(
    editors: list[StructuredRole],
    selected_candidate: Candidate,
    critiques: list[Critique],
    deterministic_report: DeterministicReport,
    state: ReflectionState,
    next_iteration: int,
) -> list[Candidate]:
    relevant_critiques = [
        critique
        for critique in critiques
        if critique.candidate_id == selected_candidate.candidate_id
    ]

    candidates: list[Candidate] = []

    previous_editor_answers: list[str] = []

    for index, editor in enumerate(editors):
        diversity_instruction = ""

        if previous_editor_answers:
            diversity_instruction = f"""
            Another editor already proposed this revision:
            {safe_json_dumps(previous_editor_answers)}

            Produce an independently revised version.
            Do not copy its structure automatically.
            """

        result = editor.run_structured(
            instructions=f"""
            Revise the selected candidate.

            User request:
            {state.user_request}

            Source material:
            {state.source_material}

            Requirements:
            {safe_json_dumps(state.requirements)}

            Selected candidate:
            {selected_candidate.content}

            Critiques:
            {safe_json_dumps([
                {
                    "critic": critique.critic_role,
                    "scores": critique.scores,
                    "issues": critique.issues,
                    "strengths": critique.strengths,
                }
                for critique in relevant_critiques
            ])}

            Deterministic report:
            {safe_json_dumps({
                "score": deterministic_report.score,
                "issues": deterministic_report.issues,
                "metrics": deterministic_report.metrics,
            })}

            {diversity_instruction}

            Instructions:
            - Preserve correct and useful content.
            - Correct all valid critical and major issues.
            - Do not blindly apply contradictory feedback.
            - State uncertainty where the source is insufficient.
            - Produce a complete standalone answer.
            - Do not mention critics, judges, models, or internal iterations.
            """,
            expected_schema=REVISION_SCHEMA,
        )

        answer = str(result.get("answer", "")).strip()

        if not answer:
            continue

        candidates.append(
            Candidate(
                candidate_id=f"i{next_iteration}-r{index + 1}",
                content=answer,
                source_role=str(editor.role_name),
                iteration=next_iteration,
                strategy="revision",
                assumptions=[
                    str(item)
                    for item in result.get("remaining_uncertainties", [])
                ],
            )
        )

        previous_editor_answers.append(answer)

    # Conserver aussi le meilleur candidat précédent permet d'éviter
    # qu'une révision dégradée gagne par défaut.
    incumbent = Candidate(
        candidate_id=f"i{next_iteration}-incumbent",
        content=selected_candidate.content,
        source_role="incumbent",
        iteration=next_iteration,
        strategy="preserve_previous_best",
        assumptions=list(selected_candidate.assumptions),
        score=selected_candidate.score,
    )

    candidates.append(incumbent)

    return deduplicate_candidates(candidates)


# ============================================================
# Audit final
# ============================================================

FINAL_AUDIT_SCHEMA = {
    "publish": True,
    "score": 0,
    "critical_issues": ["string"],
    "major_issues": ["string"],
    "reason": "string",
    "confidence": 0.0,
}


def final_audit(
    auditors: list[StructuredRole],
    candidate: Candidate,
    state: ReflectionState,
) -> dict[str, Any]:
    reports: list[dict[str, Any]] = []

    for auditor in auditors:
        report = auditor.run_structured(
            instructions=f"""
            Perform a final publication audit.

            User request:
            {state.user_request}

            Source material:
            {state.source_material}

            Requirements:
            {safe_json_dumps(state.requirements)}

            Proposed final answer:
            {candidate.content}

            Reject publication if:
            - the answer contains a factual or logical error;
            - an explicit requirement is omitted;
            - important uncertainty is concealed;
            - it invents information absent from the supplied source;
            - it exposes internal hidden reasoning;
            - it contains unresolved critical defects.

            Do not rewrite the answer.
            """,
            expected_schema=FINAL_AUDIT_SCHEMA,
        )

        reports.append(report)

    publish_votes = [
        bool(report.get("publish", False))
        for report in reports
    ]

    scores = [
        clamp(float(report.get("score", 0.0)), 0.0, 10.0)
        for report in reports
    ]

    critical_issues = [
        str(issue)
        for report in reports
        for issue in report.get("critical_issues", [])
    ]

    major_issues = [
        str(issue)
        for report in reports
        for issue in report.get("major_issues", [])
    ]

    return {
        "publish": (
            bool(publish_votes)
            and all(publish_votes)
            and not critical_issues
            and median(scores) >= MINIMUM_ACCEPTED_SCORE
        ),
        "score": median(scores),
        "critical_issues": critical_issues,
        "major_issues": major_issues,
        "reports": reports,
    }


# ============================================================
# Contrôleur principal
# ============================================================

class MultiLLMReflectionSystem:
    def __init__(self):
        (
            self.generators,
            self.critics,
            self.verifiers,
            self.judges,
            self.editors,
            self.auditors,
        ) = create_agents()

    def solve(
        self,
        user_request: str,
        source_material: str,
        requirements: list[str],
    ) -> ReflectionState:
        state = ReflectionState(
            user_request=user_request,
            source_material=source_material,
            requirements=requirements,
        )

        candidates = generate_initial_candidates(
            generators=self.generators,
            state=state,
            iteration=1,
        )

        previous_best_score = -math.inf

        for iteration in range(1, MAX_ITERATIONS + 1):
            if not candidates:
                state.finish_reason = "Aucun candidat exploitable n'a été généré."
                break

            critiques = run_critiques(
                critics=self.critics,
                candidates=candidates,
                state=state,
            )

            verifier_critiques = run_verifiers(
                verifiers=self.verifiers,
                candidates=candidates,
                state=state,
                critiques=critiques,
            )

            critiques.extend(verifier_critiques)

            deterministic_reports: dict[str, DeterministicReport] = {}

            for candidate in candidates:
                report = deterministic_checks(
                    candidate=candidate,
                    requirements=state.requirements,
                )

                deterministic_reports[candidate.candidate_id] = report

                candidate.score = aggregate_candidate_score(
                    candidate=candidate,
                    critiques=critiques,
                    deterministic_report=report,
                )

            selected_id, arbitration = judge_candidates(
                judges=self.judges,
                candidates=candidates,
                critiques=critiques,
                deterministic_reports=deterministic_reports,
                state=state,
            )

            selected_candidate = next(
                (
                    candidate
                    for candidate in candidates
                    if candidate.candidate_id == selected_id
                ),
                max(candidates, key=lambda item: item.score),
            )

            # L'arbitre ne peut pas forcer un candidat très inférieur.
            computed_best = max(candidates, key=lambda item: item.score)

            if selected_candidate.score + 0.75 < computed_best.score:
                selected_candidate = computed_best
                selected_id = computed_best.candidate_id
                arbitration["override"] = (
                    "Le choix de l'arbitre était trop inférieur "
                    "au meilleur score consolidé."
                )

            if selected_candidate.score > state.best_score:
                state.best_candidate = selected_candidate
                state.best_score = selected_candidate.score

            critical_count = count_issues(
                candidate_id=selected_candidate.candidate_id,
                critiques=critiques,
                severity="critical",
            )

            major_count = count_issues(
                candidate_id=selected_candidate.candidate_id,
                critiques=critiques,
                severity="major",
            )

            deterministic_passed = deterministic_reports[
                selected_candidate.candidate_id
            ].passed

            score_gain = (
                selected_candidate.score - previous_best_score
                if previous_best_score != -math.inf
                else None
            )

            quality_reached = (
                selected_candidate.score >= MINIMUM_ACCEPTED_SCORE
                and critical_count <= MAXIMUM_CRITICAL_ISSUES
                and deterministic_passed
            )

            decision = "revise"
            reason = (
                "Le score ou les contrôles ne permettent pas encore "
                "une publication sûre."
            )

            if quality_reached:
                audit = final_audit(
                    auditors=self.auditors,
                    candidate=selected_candidate,
                    state=state,
                )

                if audit["publish"]:
                    decision = "finish"
                    reason = "Le candidat a passé l'audit final indépendant."
                else:
                    reason = (
                        "Le seuil interne est atteint, mais l'audit final "
                        "a détecté des risques résiduels."
                    )
            else:
                audit = None

            if (
                decision != "finish"
                and score_gain is not None
                and score_gain < MINIMUM_SCORE_GAIN
                and iteration >= 2
            ):
                reason += (
                    " La progression est faible ; une dernière stratégie "
                    "alternative sera tentée si une itération reste disponible."
                )

            state.iterations.append(
                IterationRecord(
                    iteration=iteration,
                    candidates=candidates,
                    critiques=critiques,
                    deterministic_reports=deterministic_reports,
                    selected_candidate_id=selected_candidate.candidate_id,
                    selected_score=selected_candidate.score,
                    decision=decision,
                    reason=reason,
                )
            )

            if decision == "finish":
                state.final_answer = selected_candidate.content
                state.finish_reason = reason
                break

            if iteration >= MAX_ITERATIONS:
                break

            previous_best_score = max(
                previous_best_score,
                selected_candidate.score,
            )

            candidates = build_revision_candidates(
                editors=self.editors,
                selected_candidate=selected_candidate,
                critiques=critiques,
                deterministic_report=deterministic_reports[
                    selected_candidate.candidate_id
                ],
                state=state,
                next_iteration=iteration + 1,
            )

            # À la dernière tentative, on ajoute un nouveau générateur depuis zéro.
            # Cela évite que toutes les révisions restent enfermées dans le même cadre.
            if iteration == MAX_ITERATIONS - 1:
                fresh_candidates = generate_initial_candidates(
                    generators=self.generators,
                    state=state,
                    iteration=iteration + 1,
                )

                for fresh in fresh_candidates:
                    fresh.candidate_id = (
                        f"{fresh.candidate_id}-fresh-restart"
                    )

                candidates.extend(fresh_candidates)
                candidates = deduplicate_candidates(candidates)

        if state.final_answer is None:
            self._finish_with_best_available(state)

        return state

    def _finish_with_best_available(
        self,
        state: ReflectionState,
    ):
        """
        Ne publie pas automatiquement une réponse dangereuse.

        Si aucun candidat n'a atteint le seuil, le système retourne
        la meilleure version avec une mention d'incertitude contrôlée.
        """
        if state.best_candidate is None:
            state.final_answer = (
                "Je ne dispose pas d'une réponse suffisamment fiable "
                "à partir des éléments fournis."
            )
            state.finish_reason = (
                state.finish_reason
                or "Aucun candidat fiable n'a été produit."
            )
            return

        audit = final_audit(
            auditors=self.auditors,
            candidate=state.best_candidate,
            state=state,
        )

        if audit["critical_issues"]:
            state.final_answer = (
                "Les éléments fournis ne permettent pas de produire une réponse "
                "fiable sans risquer d'introduire des erreurs. "
                "Les principaux points non résolus sont : "
                + "; ".join(audit["critical_issues"])
            )
            state.finish_reason = (
                "Le meilleur candidat conservait des problèmes critiques."
            )
            return

        state.final_answer = state.best_candidate.content
        state.finish_reason = (
            "Nombre maximal d'itérations atteint ; "
            "publication de la meilleure version auditée disponible."
        )


# ============================================================
# Rapport de diagnostic
# ============================================================

def build_debug_report(state: ReflectionState) -> dict[str, Any]:
    return {
        "finish_reason": state.finish_reason,
        "best_score": state.best_score,
        "best_candidate_id": (
            state.best_candidate.candidate_id
            if state.best_candidate
            else None
        ),
        "iterations": [
            {
                "iteration": record.iteration,
                "candidate_scores": {
                    candidate.candidate_id: candidate.score
                    for candidate in record.candidates
                },
                "selected_candidate_id": record.selected_candidate_id,
                "selected_score": record.selected_score,
                "decision": record.decision,
                "reason": record.reason,
                "critical_issues": {
                    candidate.candidate_id: count_issues(
                        candidate_id=candidate.candidate_id,
                        critiques=record.critiques,
                        severity="critical",
                    )
                    for candidate in record.candidates
                },
                "major_issues": {
                    candidate.candidate_id: count_issues(
                        candidate_id=candidate.candidate_id,
                        critiques=record.critiques,
                        severity="major",
                    )
                    for candidate in record.candidates
                },
            }
            for record in state.iterations
        ],
    }


# ============================================================
# Exemple
# ============================================================

def main():
    source_material = """
    - Nightly invoice export failed for every tenant at 02:05.
    - The scheduler started the export job normally.
    - The processing queue grew from 120 to 7800 jobs in 30 minutes.
    - The first failing downstream log says: payment-api 401 invalid_client.
    - A service credential was rotated at 01:50.
    - Manual retry succeeds after refreshing the payment-api token.
    """

    user_request = """
    Analyse l'incident, identifie la cause racine la plus probable,
    distingue les faits des hypothèses et propose une action immédiate
    ainsi que des mesures préventives.
    """

    requirements = [
        "identifier la cause racine la plus probable",
        "distinguer les faits des hypothèses",
        "proposer une action immédiate",
        "proposer des mesures préventives",
        "indiquer le niveau d'incertitude",
    ]

    system = MultiLLMReflectionSystem()

    state = system.solve(
        user_request=user_request,
        source_material=source_material,
        requirements=requirements,
    )

    print("\n=== RÉPONSE FINALE ===\n")
    print(state.final_answer)

    print("\n=== RAPPORT INTERNE ===\n")
    print(
        json.dumps(
            build_debug_report(state),
            ensure_ascii=False,
            indent=2,
        )
    )


if __name__ == "__main__":
    main()
