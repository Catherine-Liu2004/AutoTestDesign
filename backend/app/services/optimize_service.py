"""Test suite optimization service — identify redundant/low-value test cases."""
from app.models.models import TestCase, Requirement


class OptimizeService:
    def optimize_risk_based(
        self,
        cases: list[TestCase],
        reqs: dict[str, Requirement],
    ) -> list[tuple[TestCase, str]]:
        """Risk-based: flag low-priority cases whose requirement has low risk score."""
        candidates = []
        for tc in cases:
            req = reqs.get(tc.req_id)
            if not req:
                continue
            risk = req.risk_score or 0
            if tc.priority == "low" and risk < 4.0:
                candidates.append((
                    tc,
                    f"Low priority case for low-risk requirement (risk={risk:.1f})",
                ))
            elif tc.status == "pass" and tc.priority == "low" and risk < 5.0:
                candidates.append((
                    tc,
                    f"Already passing low-priority case for risk={risk:.1f}",
                ))
        return candidates

    def optimize_coverage_efficiency(
        self, cases: list[TestCase]
    ) -> list[tuple[TestCase, str]]:
        """Coverage efficiency: flag duplicate titles or near-duplicate input_data."""
        candidates = []
        seen_titles: dict[str, str] = {}  # normalized_title -> first tc_id
        seen_inputs: dict[str, str] = {}   # json repr -> first tc_id

        for tc in cases:
            norm_title = tc.title.lower().strip()
            # Check duplicate title (same technique)
            key = f"{tc.technique}::{norm_title}"
            if key in seen_titles:
                candidates.append((
                    tc,
                    f"Duplicate title under same technique (first occurrence: {seen_titles[key][:8]}…)",
                ))
                continue
            seen_titles[key] = tc.id

            # Check duplicate input_data
            if tc.input_data:
                import json
                inp_key = f"{tc.technique}::{json.dumps(tc.input_data, sort_keys=True)}"
                if inp_key in seen_inputs:
                    candidates.append((
                        tc,
                        f"Identical input_data as TC {seen_inputs[inp_key][:8]}… — potential redundancy",
                    ))
                    continue
                seen_inputs[inp_key] = tc.id

        return candidates


optimize_service = OptimizeService()
