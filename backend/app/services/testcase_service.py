import asyncio
from app.core.llm import llm_client
from app.models.models import Requirement, TestCase, TestSuite

# ── Prompt Templates ──────────────────────────────────────────────────────────

EP_SYSTEM_PROMPT = """You are a software testing expert applying Equivalence Partitioning (EP).
Given a requirement, generate test cases covering valid and invalid equivalence classes.
Return JSON: {"test_cases": [{"title": str, "preconditions": str, "input_data": {}, "expected_result": str, "priority": "high"|"medium"|"low"}]}
Generate 3-5 test cases. Return ONLY valid JSON."""

BVA_SYSTEM_PROMPT = """You are a software testing expert applying Boundary Value Analysis (BVA).
Given a requirement, generate test cases at boundary values (min, max, just inside/outside boundaries).
Return JSON: {"test_cases": [{"title": str, "preconditions": str, "input_data": {}, "expected_result": str, "priority": "high"|"medium"|"low"}]}
Generate 3-5 test cases. Return ONLY valid JSON."""

DT_SYSTEM_PROMPT = """You are a software testing expert applying Decision Table testing.
Given a requirement, identify conditions and actions, then generate test cases for condition combinations.
Return JSON: {"test_cases": [{"title": str, "preconditions": str, "input_data": {}, "expected_result": str, "priority": "high"|"medium"|"low"}]}
Generate 3-5 test cases. Return ONLY valid JSON."""

STATE_SYSTEM_PROMPT = """You are a software testing expert applying State Transition testing.
Given a requirement, identify system states and transitions, generate test cases for state coverage.
Return JSON: {"test_cases": [{"title": str, "preconditions": str, "input_data": {}, "expected_result": str, "priority": "high"|"medium"|"low"}]}
Generate 3-5 test cases. Return ONLY valid JSON."""

TECHNIQUE_REGISTRY: dict[str, tuple[str, str]] = {
    "equivalence_partitioning": (EP_SYSTEM_PROMPT, "EP"),
    "boundary_value_analysis": (BVA_SYSTEM_PROMPT, "BVA"),
    "decision_table": (DT_SYSTEM_PROMPT, "DT"),
    "state_transition": (STATE_SYSTEM_PROMPT, "ST"),
}


class TestCaseService:
    async def _generate_for_technique(
        self, req: Requirement, technique: str
    ) -> list[TestCase]:
        system_prompt, tech_abbr = TECHNIQUE_REGISTRY.get(
            technique, (EP_SYSTEM_PROMPT, technique[:2].upper())
        )
        try:
            result = await llm_client.complete_json(
                system_prompt=system_prompt,
                user_prompt=(
                    f"Requirement ID: {req.id}\n"
                    f"Requirement: {req.raw_text}\n"
                    f"Structured info: {req.structured or {}}"
                ),
            )
            cases = []
            for tc_data in result.get("test_cases", []):
                tc = TestCase(
                    req_id=req.id,
                    technique=technique,
                    title=tc_data.get("title", "Untitled"),
                    preconditions=tc_data.get("preconditions", ""),
                    input_data=tc_data.get("input_data", {}),
                    expected_result=tc_data.get("expected_result", ""),
                    priority=tc_data.get("priority", "medium"),
                )
                cases.append(tc)
            return cases
        except Exception:
            # Fallback: generate one placeholder test case
            return [
                TestCase(
                    req_id=req.id,
                    technique=technique,
                    title=f"[{technique}] Basic test for: {req.raw_text[:80]}",
                    preconditions="System is in initial state",
                    input_data={},
                    expected_result="System behaves as specified in requirement",
                    priority="medium",
                )
            ]

    async def generate(
        self,
        reqs: list[Requirement],
        techniques: list[str],
        include_whitebox: bool = False,
    ) -> tuple[TestSuite, list[TestCase]]:
        if include_whitebox and "state_transition" not in techniques:
            techniques = list(techniques) + ["state_transition"]

        # Generate concurrently across requirements × techniques
        tasks = [
            self._generate_for_technique(req, tech)
            for req in reqs
            for tech in techniques
        ]
        results = await asyncio.gather(*tasks)
        all_cases: list[TestCase] = [tc for sublist in results for tc in sublist]

        suite = TestSuite(
            name=f"Suite for {', '.join(r.id for r in reqs[:3])}{'...' if len(reqs) > 3 else ''}",
            req_ids=[r.id for r in reqs],
            techniques=techniques,
            tc_count=len(all_cases),
        )
        return suite, all_cases
