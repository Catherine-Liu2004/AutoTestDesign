"""Whitebox testing service — state diagram generation (Mermaid)."""
from app.core.llm import llm_client
from app.models.models import Requirement

MERMAID_SYSTEM_PROMPT = """You are a software testing expert.
Given a software requirement, generate a Mermaid stateDiagram-v2 diagram that models the key system states and transitions.

Return ONLY a JSON object in this exact format:
{
  "mermaid": "stateDiagram-v2\\n    [*] --> StateA\\n    StateA --> StateB : trigger\\n    StateB --> [*] : end"
}

Rules:
- Use `stateDiagram-v2` syntax
- Include at least 3 states with meaningful names
- Label transitions with descriptive triggers/events
- Include [*] for initial/final states where appropriate
- Keep the diagram concise but representative of the requirement
- Return ONLY valid JSON, no markdown fences"""


class WhiteboxService:
    async def generate_state_diagram(self, req: Requirement) -> str:
        """Generate a Mermaid state diagram for a requirement. Returns Mermaid text."""
        try:
            result = await llm_client.complete_json(
                system_prompt=MERMAID_SYSTEM_PROMPT,
                user_prompt=(
                    f"Requirement: {req.raw_text}\n"
                    f"Structured info: {req.structured or {}}"
                ),
            )
            return result.get("mermaid", _default_diagram(req))
        except Exception:
            return _default_diagram(req)


def _default_diagram(req: Requirement) -> str:
    name = req.raw_text[:30].replace("\n", " ")
    return (
        "stateDiagram-v2\n"
        "    [*] --> Idle\n"
        f"    Idle --> Processing : trigger ({name}...)\n"
        "    Processing --> Success : valid input\n"
        "    Processing --> Error : invalid input\n"
        "    Success --> [*]\n"
        "    Error --> Idle : retry"
    )


whitebox_service = WhiteboxService()
