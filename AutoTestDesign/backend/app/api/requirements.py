import csv
import io
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.models import Requirement
from app.schemas.schemas import (
    RequirementImportRequest,
    RequirementRead,
    RequirementUpdate,
    StructuredInfo,
)
from app.services.parse_service import ParseService

router = APIRouter(prefix="/requirements", tags=["requirements"])


@router.post("/import", response_model=list[RequirementRead])
async def import_requirements(payload: RequirementImportRequest, db: Session = Depends(get_db)):
    reqs: list[Requirement] = []

    if payload.source_type == "csv":
        import base64
        try:
            decoded = base64.b64decode(payload.content).decode("utf-8")
        except Exception:
            decoded = payload.content
        reader = csv.DictReader(io.StringIO(decoded))
        has_text_col = bool(
            reader.fieldnames
            and (
                "description" in (reader.fieldnames or [])
                or "requirement" in (reader.fieldnames or [])
            )
        )
        for row in reader:
            if has_text_col:
                text = row.get("description", "").strip() or row.get("requirement", "").strip()
            else:
                text = " | ".join(v.strip() for v in row.values() if v.strip())
            if text:
                req = Requirement(raw_text=text, source_type="csv")
                db.add(req)
                reqs.append(req)
    elif payload.source_type in ("txt", "direct"):
        paragraphs = [p.strip() for p in payload.content.split("\n\n") if p.strip()]
        if not paragraphs:
            paragraphs = [payload.content.strip()]
        for para in paragraphs:
            req = Requirement(raw_text=para, source_type=payload.source_type)
            db.add(req)
            reqs.append(req)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported source_type: {payload.source_type}")

    db.commit()
    for r in reqs:
        db.refresh(r)
    return reqs


@router.get("", response_model=list[RequirementRead])
def list_requirements(skip: int = 0, limit: int = 100, db: Session = Depends(get_db)):
    return db.query(Requirement).offset(skip).limit(limit).all()


@router.get("/{req_id}", response_model=RequirementRead)
def get_requirement(req_id: str, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return req


@router.put("/{req_id}", response_model=RequirementRead)
def update_requirement(req_id: str, payload: RequirementUpdate, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    for field, value in payload.model_dump(exclude_none=True).items():
        setattr(req, field, value)
    db.commit()
    db.refresh(req)
    return req


@router.delete("/{req_id}", status_code=204)
def delete_requirement(req_id: str, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    db.delete(req)
    db.commit()


@router.post("/{req_id}/parse", response_model=RequirementRead)
async def parse_requirement(req_id: str, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    service = ParseService()
    structured = await service.parse(req.raw_text)
    req.structured = structured
    db.commit()
    db.refresh(req)
    return req


@router.post("/parse-batch", response_model=list[RequirementRead])
async def parse_batch(db: Session = Depends(get_db)):
    reqs = db.query(Requirement).filter(Requirement.structured.is_(None)).all()
    service = ParseService()
    for req in reqs:
        structured = await service.parse(req.raw_text)
        req.structured = structured
    db.commit()
    for req in reqs:
        db.refresh(req)
    return reqs


@router.put("/{req_id}/structure", response_model=RequirementRead)
def update_structure(req_id: str, payload: StructuredInfo, db: Session = Depends(get_db)):
    req = db.query(Requirement).filter(Requirement.id == req_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Requirement not found")
    req.structured = payload.model_dump()
    db.commit()
    db.refresh(req)
    return req
