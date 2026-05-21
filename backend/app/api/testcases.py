from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import TestCase, TestSuite, Requirement
from app.schemas.schemas import (
    TestCaseCreate,
    TestCaseGenerateRequest,
    TestCaseRead,
    TestCaseUpdate,
    TestSuiteRead,
    TraceabilityMatrix,
    OracleRequest,
    OracleResponse,
    OracleResult,
)
from app.services.testcase_service import TestCaseService
from app.services.oracle_service import oracle_service

router = APIRouter(prefix="/testcases", tags=["testcases"])


@router.get("/suites", response_model=list[TestSuiteRead])
def list_test_suites(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    suites = db.query(TestSuite).order_by(TestSuite.created_at.desc()).offset(skip).limit(limit).all()
    return [TestSuiteRead.model_validate(s) for s in suites]


@router.post("", response_model=TestCaseRead, status_code=201)
def create_test_case(payload: TestCaseCreate, db: Session = Depends(get_db)):
    """Manually create a test case (not AI-generated)."""
    suite = db.query(TestSuite).filter(TestSuite.id == payload.suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="TestSuite not found")
    tc = TestCase(
        suite_id=payload.suite_id,
        req_id=payload.req_id,
        technique=payload.technique,
        title=payload.title,
        preconditions=payload.preconditions,
        input_data=payload.input_data,
        expected_result=payload.expected_result,
        priority=payload.priority,
        status="pending",
    )
    db.add(tc)
    suite.tc_count = (suite.tc_count or 0) + 1
    db.commit()
    db.refresh(tc)
    return tc


@router.post("/generate", response_model=TestSuiteRead)
async def generate_test_cases(payload: TestCaseGenerateRequest, db: Session = Depends(get_db)):
    reqs = db.query(Requirement).filter(Requirement.id.in_(payload.req_ids)).all()
    if not reqs:
        raise HTTPException(status_code=404, detail="No requirements found")

    service = TestCaseService()
    suite, cases = await service.generate(reqs, payload.techniques, payload.include_whitebox)

    db.add(suite)
    db.flush()
    for tc in cases:
        tc.suite_id = suite.id
        db.add(tc)
    suite.tc_count = len(cases)
    db.commit()
    db.refresh(suite)

    result = TestSuiteRead.model_validate(suite)
    result.test_cases = [TestCaseRead.model_validate(tc) for tc in cases]
    return result


@router.get("", response_model=list[TestCaseRead])
def list_test_cases(
    suite_id: str | None = None,
    req_id: str | None = None,
    skip: int = 0,
    limit: int = 100,
    db: Session = Depends(get_db),
):
    query = db.query(TestCase)
    if suite_id:
        query = query.filter(TestCase.suite_id == suite_id)
    if req_id:
        query = query.filter(TestCase.req_id == req_id)
    return query.offset(skip).limit(limit).all()


@router.get("/{tc_id}", response_model=TestCaseRead)
def get_test_case(tc_id: str, db: Session = Depends(get_db)):
    tc = db.query(TestCase).filter(TestCase.id == tc_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    return tc


@router.put("/{tc_id}", response_model=TestCaseRead)
def update_test_case(tc_id: str, payload: TestCaseUpdate, db: Session = Depends(get_db)):
    tc = db.query(TestCase).filter(TestCase.id == tc_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(tc, field, value)
    db.commit()
    db.refresh(tc)
    return tc


@router.delete("/{tc_id}", status_code=204)
def delete_test_case(tc_id: str, db: Session = Depends(get_db)):
    tc = db.query(TestCase).filter(TestCase.id == tc_id).first()
    if not tc:
        raise HTTPException(status_code=404, detail="TestCase not found")
    db.delete(tc)
    db.commit()


@router.post("/generate-oracle", response_model=OracleResponse)
async def generate_oracle(payload: OracleRequest, db: Session = Depends(get_db)):
    """Generate AI test oracles for a list of test cases."""
    import asyncio
    cases = db.query(TestCase).filter(TestCase.id.in_(payload.tc_ids)).all()
    if not cases:
        raise HTTPException(status_code=404, detail="No test cases found")

    async def _process(tc: TestCase) -> OracleResult:
        oracle_text = await oracle_service.generate_oracle(tc)
        tc.ai_oracle = oracle_text
        return OracleResult(
            tc_id=tc.id,
            original_expected=tc.expected_result,
            ai_oracle=oracle_text,
        )

    results = await asyncio.gather(*[_process(tc) for tc in cases])
    db.commit()
    return OracleResponse(results=list(results))
