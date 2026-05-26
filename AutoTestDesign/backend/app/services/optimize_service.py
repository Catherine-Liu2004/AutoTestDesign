"""Test suite optimization service — identify redundant/low-value test cases."""
import json
from app.models.models import TestCase, Requirement

# Risk threshold below which a requirement is considered low-risk
_LOW_RISK = 4.0
_VERY_LOW_RISK = 2.5
# Max cases considered non-redundant for the same req + technique combination
_MAX_CASES_PER_REQ_TECHNIQUE = 2


class OptimizeService:
    def optimize_risk_based(
        self,
        cases: list[TestCase],
        reqs: dict[str, Requirement],
    ) -> list[tuple[TestCase, str]]:
        """Risk-based: flag cases that are low-value relative to their requirement's risk score.

        Flags:
        - Any priority case that is already 'pass' for a low-risk requirement
        - Low-priority cases for low-risk requirements
        - Medium-priority cases for very-low-risk requirements (< 2.5)
        - Cases for requirements with no risk analysis whose priority is not 'high'
        """
        candidates = []
        seen: set[str] = set()

        def _add(tc: TestCase, reason: str) -> None:
            if tc.id not in seen:
                seen.add(tc.id)
                candidates.append((tc, reason))

        for tc in cases:
            req = reqs.get(tc.req_id)
            risk_score = (req.risk_score if req else None)
            risk_analyzed = risk_score is not None
            risk = risk_score or 0.0

            # Already passing cases for low-risk requirements are good removal candidates
            if tc.status == "pass" and tc.priority != "high":
                if not risk_analyzed or risk < _LOW_RISK:
                    _add(tc, f"Already passing {tc.priority}-priority case"
                              + (f" (risk={risk:.1f})" if risk_analyzed else " (requirement not risk-analyzed)"))
                continue

            if tc.priority == "low":
                if not risk_analyzed or risk < _LOW_RISK:
                    _add(tc, f"Low-priority case"
                              + (f" for low-risk requirement (risk={risk:.1f})" if risk_analyzed
                                 else " for un-analyzed requirement"))

            elif tc.priority == "medium" and risk < _VERY_LOW_RISK:
                _add(tc, f"Medium-priority case for very-low-risk requirement (risk={risk:.1f})")

        return candidates

    def optimize_coverage_efficiency(
        self, cases: list[TestCase]
    ) -> list[tuple[TestCase, str]]:
        """Coverage efficiency: flag duplicate / redundant test cases.

        Flags:
        - Exact duplicate titles under the same technique
        - Identical input_data under the same technique
        - Extra cases beyond _MAX_CASES_PER_REQ_TECHNIQUE for the same req+technique
          (keeps the first N, flags the rest if they are not high-priority)
        """
        candidates = []
        seen: set[str] = set()
        seen_titles: dict[str, str] = {}   # "technique::norm_title" -> first tc_id
        seen_inputs: dict[str, str] = {}   # "technique::json_inputs" -> first tc_id
        req_tech_seen: dict[str, list[str]] = {}  # "req_id::technique" -> [tc_id, ...]

        def _add(tc: TestCase, reason: str) -> None:
            if tc.id not in seen:
                seen.add(tc.id)
                candidates.append((tc, reason))

        for tc in cases:
            norm_title = tc.title.lower().strip()
            title_key = f"{tc.technique}::{norm_title}"

            if title_key in seen_titles:
                _add(tc, f"Duplicate title under same technique (first: {seen_titles[title_key][:8]}…)")
                continue
            seen_titles[title_key] = tc.id

            if tc.input_data:
                inp_key = f"{tc.technique}::{json.dumps(tc.input_data, sort_keys=True)}"
                if inp_key in seen_inputs:
                    _add(tc, f"Identical input data as TC {seen_inputs[inp_key][:8]}…")
                    continue
                seen_inputs[inp_key] = tc.id

            # Track req + technique coverage saturation
            rt_key = f"{tc.req_id}::{tc.technique}"
            bucket = req_tech_seen.setdefault(rt_key, [])
            bucket.append(tc.id)
            if len(bucket) > _MAX_CASES_PER_REQ_TECHNIQUE and tc.priority != "high":
                _add(
                    tc,
                    f"Possible coverage saturation: {len(bucket)} cases for same requirement + technique"
                    f" (keeping first {_MAX_CASES_PER_REQ_TECHNIQUE})",
                )

        return candidates


optimize_service = OptimizeService()
