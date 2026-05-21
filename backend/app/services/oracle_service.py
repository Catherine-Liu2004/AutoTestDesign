"""Test Oracle service — AI-generated expected results for test cases."""
from app.core.llm import llm_client
from app.models.models import TestCase

ORACLE_SYSTEM_PROMPT = """You are a software testing expert.
Given a test case (title, preconditions, input_data, current expected_result), generate an improved, precise test oracle — the exact expected behavior/output.

Return ONLY a JSON object:
{
  "oracle": "precise expected result / assertion statement"
}

Make the oracle:
- Specific and verifiable (mention exact values, status codes, messages where possible)
- Include both positive assertion and potential side effects
- Reference the test case context explicitly
Return ONLY valid JSON."""


class OracleService:
    async def generate_oracle(self, tc: TestCase) -> str:
        """Generate an AI test oracle for a single test case."""
        try:
            result = await llm_client.complete_json(
                system_prompt=ORACLE_SYSTEM_PROMPT,
                user_prompt=(
                    f"Test Case Title: {tc.title}\n"
                    f"Preconditions: {tc.preconditions or 'None'}\n"
                    f"Input Data: {tc.input_data or {}}\n"
                    f"Current Expected Result: {tc.expected_result}"
                ),
            )
            return result.get("oracle", tc.expected_result)
        except Exception:
            return tc.expected_result


oracle_service = OracleService()
