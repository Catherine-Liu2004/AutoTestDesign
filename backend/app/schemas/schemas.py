from datetime import datetime
from typing import Any, Optional
from pydantic import BaseModel, Field


# ── Requirement ──────────────────────────────────────────────────────────────

class RequirementImportRequest(BaseModel):
    source_type: str = Field("direct", pattern="^(csv|txt|json|direct)$")
    content: str = Field(..., min_length=1)
    file_name: Optional[str] = None


class StructuredInfo(BaseModel):
    input_fields: list[str] = []
    data_ranges: dict[str, str] = {}
    conditions: list[str] = []
    expected_actions: list[str] = []


class RequirementRead(BaseModel):
    id: str
    raw_text: str
    source_type: str
    structured: Optional[StructuredInfo] = None
    state_diagram: Optional[str] = None
    risk_score: Optional[float] = None
    priority: Optional[str] = None
    risk_rationale: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class RequirementUpdate(BaseModel):
    raw_text: Optional[str] = None
    structured: Optional[StructuredInfo] = None
    risk_score: Optional[float] = Field(None, ge=0, le=10)
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")


# ── Risk ─────────────────────────────────────────────────────────────────────

class RiskAnalyzeRequest(BaseModel):
    req_ids: list[str] = Field(default_factory=list)
    criteria: list[str] = Field(
        default=["complexity", "business_impact", "frequency_of_use"]
    )


class RiskResult(BaseModel):
    req_id: str
    risk_score: float
    priority: str
    rationale: str


class RiskReport(BaseModel):
    results: list[RiskResult]


# ── TestCase ──────────────────────────────────────────────────────────────────

class TestCaseGenerateRequest(BaseModel):
    req_ids: list[str]
    techniques: list[str] = Field(
        default=["equivalence_partitioning", "boundary_value_analysis", "decision_table"]
    )
    include_whitebox: bool = False
    coverage_criteria: Optional[str] = None


class TestCaseRead(BaseModel):
    id: str
    suite_id: Optional[str] = None
    req_id: str
    technique: str
    title: str
    preconditions: Optional[str] = None
    input_data: Optional[dict[str, Any]] = None
    expected_result: str
    actual_result: Optional[str] = None
    ai_oracle: Optional[str] = None
    status: str
    priority: str
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class TestCaseUpdate(BaseModel):
    title: Optional[str] = None
    preconditions: Optional[str] = None
    input_data: Optional[dict[str, Any]] = None
    expected_result: Optional[str] = None
    actual_result: Optional[str] = None
    status: Optional[str] = Field(None, pattern="^(pending|pass|fail)$")
    priority: Optional[str] = Field(None, pattern="^(high|medium|low)$")


class TestSuiteRead(BaseModel):
    id: str
    name: str
    req_ids: list[str]
    techniques: list[str]
    tc_count: int
    coverage_report: Optional[dict] = None
    created_at: datetime
    test_cases: list[TestCaseRead] = []

    model_config = {"from_attributes": True}


# ── Export ────────────────────────────────────────────────────────────────────

class ExportRequest(BaseModel):
    suite_id: str
    format: str = Field("excel", pattern="^(json|excel|csv)$")
    include: list[str] = Field(
        default=["test_cases", "risk_report", "traceability_matrix"]
    )


class TestCaseCreate(BaseModel):
    suite_id: str
    req_id: str
    technique: str = Field("manual", pattern="^(equivalence_partitioning|boundary_value_analysis|decision_table|state_transition|manual)$")
    title: str
    preconditions: Optional[str] = None
    input_data: Optional[dict[str, Any]] = None
    expected_result: str
    priority: str = Field("medium", pattern="^(high|medium|low)$")


class StrategyUpdateRequest(BaseModel):
    techniques: list[str]


# ── Coverage / Traceability ───────────────────────────────────────────────────

class CoverageItem(BaseModel):
    coverage_id: str
    description: str
    technique: str
    req_id: str
    tc_ids: list[str] = []


class TraceabilityMatrix(BaseModel):
    suite_id: str
    matrix: dict[str, list[str]]  # req_id -> [tc_id, ...]
    coverage_items: list[CoverageItem] = []


# ── Sprint 4 — Whitebox / Oracle / Optimize ──────────────────────────────────

class StateDiagramResponse(BaseModel):
    req_id: str
    mermaid: str  # Mermaid stateDiagram-v2 text


class OracleRequest(BaseModel):
    tc_ids: list[str]


class OracleResult(BaseModel):
    tc_id: str
    original_expected: str
    ai_oracle: str


class OracleResponse(BaseModel):
    results: list[OracleResult]


class OptimizeRequest(BaseModel):
    suite_id: str
    strategy: str = Field("risk_based", pattern="^(risk_based|coverage_efficiency)$")


class OptimizeCandidate(BaseModel):
    tc_id: str
    title: str
    reason: str


class OptimizeResponse(BaseModel):
    suite_id: str
    strategy: str
    candidates: list[OptimizeCandidate]
    total_cases: int
    removable_count: int
