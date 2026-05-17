from app.core.llm import llm_client
from app.models.models import Requirement
from app.schemas.schemas import RiskResult

RISK_SYSTEM_PROMPT = """You are a software testing risk analyst. Given a software requirement,
evaluate its risk score (0.0–10.0) and testing priority based on:
- complexity: How complex is the logic?
- business_impact: How critical is this to the business?
- frequency_of_use: How often will this feature be used?

Return JSON with keys: risk_score (float 0-10), priority ("high"|"medium"|"low"), rationale (string).
Thresholds: high >= 7.0, medium >= 4.0, low < 4.0.
Return ONLY valid JSON."""


def _normalize_score(score: float) -> float:
    return max(0.0, min(10.0, round(score, 2)))


def _score_to_priority(score: float) -> str:
    if score >= 7.0:
        return "high"
    if score >= 4.0:
        return "medium"
    return "low"


class RiskService:
    async def analyze(self, req: Requirement, criteria: list[str]) -> RiskResult:
        try:
            result = await llm_client.complete_json(
                system_prompt=RISK_SYSTEM_PROMPT,
                user_prompt=(
                    f"Requirement ID: {req.id}\n"
                    f"Text: {req.raw_text}\n"
                    f"Evaluation criteria: {', '.join(criteria)}"
                ),
            )
            score = _normalize_score(float(result.get("risk_score", 5.0)))
            priority = result.get("priority", _score_to_priority(score))
            if priority not in ("high", "medium", "low"):
                priority = _score_to_priority(score)
            return RiskResult(
                req_id=req.id,
                risk_score=score,
                priority=priority,
                rationale=result.get("rationale", ""),
            )
        except Exception:
            score = 5.0
            return RiskResult(
                req_id=req.id,
                risk_score=score,
                priority=_score_to_priority(score),
                rationale="Risk analysis unavailable (LLM error); defaulting to medium risk.",
            )
