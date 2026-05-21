"""Coverage routes: traceability matrix and strategy update."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import TestCase, TestSuite, Requirement
from app.schemas.schemas import (
    StrategyUpdateRequest,
    TestCaseRead,
    TestSuiteRead,
    TraceabilityMatrix,
)
from app.services.testcase_service import TestCaseService

router = APIRouter(prefix="/coverage", tags=["coverage"])


@router.get("/{suite_id}/traceability", response_model=TraceabilityMatrix)
def get_traceability(suite_id: str, db: Session = Depends(get_db)):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="TestSuite not found")

    cases = db.query(TestCase).filter(TestCase.suite_id == suite_id).all()
    matrix: dict[str, list[str]] = {}
    for tc in cases:
        matrix.setdefault(tc.req_id, []).append(tc.id)

    return TraceabilityMatrix(suite_id=suite_id, matrix=matrix)


@router.put("/{suite_id}/strategy", response_model=TestSuiteRead)
async def update_strategy(
    suite_id: str,
    payload: StrategyUpdateRequest,
    db: Session = Depends(get_db),
):
    suite = db.query(TestSuite).filter(TestSuite.id == suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="TestSuite not found")

    req_ids = suite.req_ids or []
    reqs = db.query(Requirement).filter(Requirement.id.in_(req_ids)).all()
    if not reqs:
        raise HTTPException(status_code=404, detail="No requirements found for this suite")

    # Delete existing cases and regenerate with new techniques
    db.query(TestCase).filter(TestCase.suite_id == suite_id).delete()

    service = TestCaseService()
    _, new_cases = await service.generate(reqs, payload.techniques, False)
    for tc in new_cases:
        tc.suite_id = suite_id
        db.add(tc)

    suite.techniques = payload.techniques
    suite.tc_count = len(new_cases)
    db.commit()
    db.refresh(suite)

    result = TestSuiteRead.model_validate(suite)
    cases = db.query(TestCase).filter(TestCase.suite_id == suite_id).all()
    result.test_cases = [TestCaseRead.model_validate(tc) for tc in cases]
    return result
