"""Test suite optimization routes."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import TestCase, TestSuite, Requirement
from app.schemas.schemas import OptimizeRequest, OptimizeResponse, OptimizeCandidate
from app.services.optimize_service import optimize_service

router = APIRouter(prefix="/optimize", tags=["optimize"])


@router.post("", response_model=OptimizeResponse)
def optimize_suite(payload: OptimizeRequest, db: Session = Depends(get_db)):
    """Analyze a test suite and return optimization candidates."""
    suite = db.query(TestSuite).filter(TestSuite.id == payload.suite_id).first()
    if not suite:
        raise HTTPException(status_code=404, detail="TestSuite not found")

    cases = db.query(TestCase).filter(TestCase.suite_id == payload.suite_id).all()
    if not cases:
        return OptimizeResponse(
            suite_id=payload.suite_id,
            strategy=payload.strategy,
            candidates=[],
            total_cases=0,
            removable_count=0,
        )

    if payload.strategy == "risk_based":
        req_ids = list({tc.req_id for tc in cases})
        reqs_list = db.query(Requirement).filter(Requirement.id.in_(req_ids)).all()
        reqs = {r.id: r for r in reqs_list}
        raw_candidates = optimize_service.optimize_risk_based(cases, reqs)
    else:
        raw_candidates = optimize_service.optimize_coverage_efficiency(cases)

    candidate_objs = [
        OptimizeCandidate(tc_id=tc.id, title=tc.title, reason=reason)
        for tc, reason in raw_candidates
    ]

    return OptimizeResponse(
        suite_id=payload.suite_id,
        strategy=payload.strategy,
        candidates=candidate_objs,
        total_cases=len(cases),
        removable_count=len(candidate_objs),
    )
