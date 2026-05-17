from app.core.llm import llm_client

PARSE_SYSTEM_PROMPT = """You are a software testing expert. Given a software requirement text, 
extract structured information in JSON format with exactly these keys:
- input_fields: list of input field names (strings)
- data_ranges: object mapping field names to their valid data ranges/constraints (strings)
- conditions: list of conditions or constraints that affect behavior (strings)
- expected_actions: list of expected system behaviors or outputs (strings)

Return ONLY valid JSON, no explanation."""


class ParseService:
    async def parse(self, raw_text: str) -> dict:
        try:
            result = await llm_client.complete_json(
                system_prompt=PARSE_SYSTEM_PROMPT,
                user_prompt=f"Requirement: {raw_text}",
            )
            return {
                "input_fields": result.get("input_fields", []),
                "data_ranges": result.get("data_ranges", {}),
                "conditions": result.get("conditions", []),
                "expected_actions": result.get("expected_actions", []),
            }
        except Exception:
            # Fallback: return minimal structure
            return {
                "input_fields": [],
                "data_ranges": {},
                "conditions": [],
                "expected_actions": [raw_text],
            }
