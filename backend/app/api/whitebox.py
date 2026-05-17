"""Whitebox testing routes — state diagram generation."""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Requirement
from app.schemas.schemas import StateDiagramResponse
from app.services.whitebox_service import whitebox_service

router = APIRouter(prefix="/whitebox", tags=["whitebox"])


@router.post("/requirements/{req_id}/state-diagram", response_model=StateDiagramResponse)
async def generate_state_diagram(req_id: str, db: Session = Depends(get_db)):
    """Generate a Mermaid stateDiagram-v2 for a requirement and persist it."""
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")

    diagram = await whitebox_service.generate_state_diagram(req)
    req.state_diagram = diagram
    db.commit()
    db.refresh(req)

    return StateDiagramResponse(req_id=req_id, mermaid=diagram)


@router.get("/requirements/{req_id}/state-diagram", response_model=StateDiagramResponse)
def get_state_diagram(req_id: str, db: Session = Depends(get_db)):
    """Return cached state diagram (or 404 if not yet generated)."""
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    if not req.state_diagram:
        raise HTTPException(status_code=404, detail="State diagram not yet generated")
    return StateDiagramResponse(req_id=req_id, mermaid=req.state_diagram)
