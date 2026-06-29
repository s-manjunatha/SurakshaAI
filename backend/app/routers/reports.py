import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.database import get_db
from app.auth import get_current_user
from app.models import User, FIR, Evidence, PoliceStation, Location
from services.ai.groq_service import groq_service
from services.reports.pdf_service import pdf_service

router = APIRouter(prefix="/reports", tags=["PDF Reports"])


@router.get("/fir/{fir_id}/pdf")
async def generate_fir_pdf(fir_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(FIR, PoliceStation.district, PoliceStation.name)
        .join(PoliceStation).where(FIR.id == fir_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="FIR not found")

    fir, district, station_name = row
    ev_result = await db.execute(select(Evidence).where(Evidence.fir_id == fir_id))
    evidence = [{"evidence_type": e.evidence_type.value, "description": e.description, "is_verified": e.is_verified} for e in ev_result.scalars()]

    fir_data = {
        "fir_number": fir.fir_number, "crime_type": fir.crime_type.value,
        "status": fir.status.value, "priority": fir.priority.value,
        "incident_date": fir.incident_date.isoformat(), "district": district,
        "title": fir.title, "description": fir.description, "summary": fir.summary,
    }

    ai_content = {}
    try:
        ai_content = await groq_service.generate_report_content({"fir": fir_data, "evidence": evidence})
    except Exception:
        ai_content = {"executive_summary": fir.summary or fir.description}

    timeline = [
        {"date": fir.incident_date.strftime("%d %b %Y"), "event": "Incident occurred"},
        {"date": fir.registered_date.strftime("%d %b %Y"), "event": f"FIR registered at {station_name}"},
    ]

    report_data = {"fir": fir_data, "evidence": evidence, "ai_content": ai_content, "timeline": timeline}
    pdf_bytes = pdf_service.generate_investigation_report(report_data)

    return Response(
        content=pdf_bytes,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=SurakshAI_Report_{fir.fir_number}.pdf"},
    )
