from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Requirement
from app.schemas.schemas import RiskAnalyzeRequest, RiskReport, RiskResult, RequirementUpdate
from app.services.risk_service import RiskService

router = APIRouter(prefix="/risk", tags=["risk"])


@router.post("/analyze", response_model=RiskReport)
async def analyze_risk(payload: RiskAnalyzeRequest, db: Session = Depends(get_db)):
    if payload.req_ids:
        reqs = db.query(Requirement).filter(Requirement.id.in_(payload.req_ids)).all()
    else:
        reqs = db.query(Requirement).all()

    if not reqs:
        raise HTTPException(status_code=404, detail="No requirements found")

    service = RiskService()
    results: list[RiskResult] = []
    for req in reqs:
        result = await service.analyze(req, payload.criteria)
        req.risk_score = result.risk_score
        req.priority = result.priority
        req.risk_rationale = result.rationale
        results.append(result)

    db.commit()
    return RiskReport(results=results)


@router.get("/report", response_model=RiskReport)
def get_risk_report(db: Session = Depends(get_db)):
    reqs = db.query(Requirement).filter(Requirement.risk_score.isnot(None)).all()
    results = [
        RiskResult(
            req_id=r.id,
            risk_score=r.risk_score,
            priority=r.priority or "medium",
            rationale=r.risk_rationale or "",
        )
        for r in reqs
    ]
    return RiskReport(results=results)


@router.put("/{req_id}", response_model=RiskResult)
def update_risk(req_id: str, payload: RequirementUpdate, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if payload.risk_score is not None:
        req.risk_score = payload.risk_score
    if payload.priority is not None:
        req.priority = payload.priority
    db.commit()
    db.refresh(req)
    return RiskResult(
        req_id=req.id,
        risk_score=req.risk_score or 0.0,
        priority=req.priority or "medium",
        rationale=req.risk_rationale or "",
    )
