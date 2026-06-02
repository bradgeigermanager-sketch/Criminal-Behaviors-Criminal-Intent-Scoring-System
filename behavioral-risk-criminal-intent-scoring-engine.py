```python
from dataclasses import dataclass
from typing import Dict, Literal

RiskLevel = Literal["Low", "Elevated", "Concerning", "High", "Critical"]


# -----------------------------
# Weights per indicator category
# -----------------------------

CORE_WEIGHTS = {
    "personalGrievance": 3,
    "weaponsBehavior": 4,
    "explosivesInterest": 4,
    "massAttackFascination": 3,
    "behavioralEscalation": 3,
    "lifeStressors": 2,
    "targetIdentification": 4,
    "policyViolations": 2,
}

CRIMINAL_INTENT_WEIGHTS = {
    "surveillanceBehavior": 3,
    "acquisitionOfTools": 3,
    "expressedIntent": 4,
    "ideationOrFixation": 3,
    "boundaryTesting": 2,
}

VIOLENCE_RISK_WEIGHTS = {
    "threateningStatements": 4,
    "leakageOfIntent": 4,
    "interpersonalConflict": 3,
    "emotionalDysregulation": 3,
    "recentLossOrTrauma": 2,
    "isolationOrWithdrawal": 2,
}

PRE_INCIDENT_WEIGHTS = {
    "unusualTravel": 2,
    "suddenFinancialChanges": 2,
    "attemptsToProcureSensitiveInfo": 3,
    "changesInRoutine": 2,
    "communicationsChanges": 2,
}


# -----------------------------
# Risk banding
# -----------------------------

def risk_level_from_score(score: float, max_score: float) -> RiskLevel:
    """
    Map a score to a risk band using the same style as the core model.
    Thresholds are proportional to the maximum possible score.
    """
    # Use the core model’s 0–72 bands as proportions
    # 0–12, 13–24, 25–40, 41–55, 56–72
    band_edges = [12/72, 24/72, 40/72, 55/72]  # proportions
    p = score / max_score if max_score > 0 else 0.0

    if p <= band_edges[0]:
        return "Low"
    elif p <= band_edges[1]:
        return "Elevated"
    elif p <= band_edges[2]:
        return "Concerning"
    elif p <= band_edges[3]:
        return "High"
    else:
        return "Critical"


def weighted_score(indicators: Dict[str, int], weights: Dict[str, int]) -> float:
    """
    Compute a weighted score given indicator values (0–3) and weights.
    Missing indicators default to 0.
    """
    score = 0.0
    for key, w in weights.items():
        v = indicators.get(key, 0)
        score += v * w
    return score


def max_possible_score(weights: Dict[str, int]) -> int:
    """
    Maximum possible score for a module (all indicators at 3).
    """
    return 3 * sum(weights.values())


# -----------------------------
# Module scoring functions
# -----------------------------

@dataclass
class ModuleScore:
    score: float
    max_score: float
    risk_level: RiskLevel


def score_core_behavioral_risk(indicators: Dict[str, int]) -> ModuleScore:
    s = weighted_score(indicators, CORE_WEIGHTS)
    m = max_possible_score(CORE_WEIGHTS)
    return ModuleScore(score=s, max_score=m, risk_level=risk_level_from_score(s, m))


def score_criminal_intent(indicators: Dict[str, int]) -> ModuleScore:
    s = weighted_score(indicators, CRIMINAL_INTENT_WEIGHTS)
    m = max_possible_score(CRIMINAL_INTENT_WEIGHTS)
    return ModuleScore(score=s, max_score=m, risk_level=risk_level_from_score(s, m))


def score_violence_risk(indicators: Dict[str, int]) -> ModuleScore:
    s = weighted_score(indicators, VIOLENCE_RISK_WEIGHTS)
    m = max_possible_score(VIOLENCE_RISK_WEIGHTS)
    return ModuleScore(score=s, max_score=m, risk_level=risk_level_from_score(s, m))


def score_pre_incident(indicators: Dict[str, int]) -> ModuleScore:
    s = weighted_score(indicators, PRE_INCIDENT_WEIGHTS)
    m = max_possible_score(PRE_INCIDENT_WEIGHTS)
    return ModuleScore(score=s, max_score=m, risk_level=risk_level_from_score(s, m))


# -----------------------------
# Unified case scoring
# -----------------------------

@dataclass
class CaseScore:
    subject_id: str
    module_scores: Dict[str, ModuleScore]
    total_score: float
    total_max_score: float
    overall_risk_level: RiskLevel


def score_case(
    subject_id: str,
    core_indicators: Dict[str, int] | None = None,
    intent_indicators: Dict[str, int] | None = None,
    violence_indicators: Dict[str, int] | None = None,
    pre_incident_indicators: Dict[str, int] | None = None,
) -> CaseScore:
    module_scores: Dict[str, ModuleScore] = {}
    total_score = 0.0
    total_max = 0.0

    if core_indicators is not None:
        ms = score_core_behavioral_risk(core_indicators)
        module_scores["CoreBehavioralRisk"] = ms
        total_score += ms.score
        total_max += ms.max_score

    if intent_indicators is not None:
        ms = score_criminal_intent(intent_indicators)
        module_scores["CriminalIntentIndicators"] = ms
        total_score += ms.score
        total_max += ms.max_score

    if violence_indicators is not None:
        ms = score_violence_risk(violence_indicators)
        module_scores["ViolenceRiskIndicators"] = ms
        total_score += ms.score
        total_max += ms.max_score

    if pre_incident_indicators is not None:
        ms = score_pre_incident(pre_incident_indicators)
        module_scores["PreIncidentBehavior"] = ms
        total_score += ms.score
        total_max += ms.max_score

    overall_level = risk_level_from_score(total_score, total_max) if total_max > 0 else "Low"

    return CaseScore(
        subject_id=subject_id,
        module_scores=module_scores,
        total_score=total_score,
        total_max_score=total_max,
        overall_risk_level=overall_level,
    )


# -----------------------------
# Example usage
# -----------------------------
if __name__ == "__main__":
    core = {
        "personalGrievance": 2,
        "weaponsBehavior": 1,
        "explosivesInterest": 0,
        "massAttackFascination": 1,
        "behavioralEscalation": 2,
        "lifeStressors": 2,
        "targetIdentification": 1,
        "policyViolations": 1,
    }

    intent = {
        "surveillanceBehavior": 1,
        "acquisitionOfTools": 2,
        "expressedIntent": 1,
        "ideationOrFixation": 2,
        "boundaryTesting": 1,
    }

    violence = {
        "threateningStatements": 1,
        "leakageOfIntent": 1,
        "interpersonalConflict": 2,
        "emotionalDysregulation": 2,
        "recentLossOrTrauma": 1,
        "isolationOrWithdrawal": 1,
    }

    pre_incident = {
        "unusualTravel": 0,
        "suddenFinancialChanges": 1,
        "attemptsToProcureSensitiveInfo": 1,
        "changesInRoutine": 1,
        "communicationsChanges": 1,
    }

    case = score_case(
        subject_id="SUBJ-001",
        core_indicators=core,
        intent_indicators=intent,
        violence_indicators=violence,
        pre_incident_indicators=pre_incident,
    )

    print("Subject:", case.subject_id)
    print("Total score:", case.total_score, "/", case.total_max_score)
    print("Overall risk:", case.overall_risk_level)
    for name, ms in case.module_scores.items():
        print(f"{name}: {ms.score}/{ms.max_score} → {ms.risk_level}")
```
