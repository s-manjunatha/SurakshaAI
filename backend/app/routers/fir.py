from uuid import UUID
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, and_, or_, text
from typing import Optional

from app.database import get_db
from app.auth import get_current_user, require_permission, log_audit
from app.models import User, FIR, PoliceStation, Location, Evidence, FIRCriminal, FIRVictim, Criminal, Victim, CrimeType, FIRStatus, FIRPriority
from app.schemas import FIRCreate, FIRUpdate, FIRResponse, FIRDetailResponse, FIRFilter, PaginatedResponse, EvidenceResponse, CriminalBrief, VictimBrief

router = APIRouter(prefix="/fir", tags=["FIR Management"])

SCHEMA_CONTEXT = """
Tables: fir, police_stations, criminals, victims, evidence, locations, fir_criminals, fir_victims
fir columns: id, fir_number, station_id, crime_type, status, priority, title, description, incident_date, is_solved
police_stations: id, name, code, district
locations: id, district, latitude, longitude
"""


async def _fir_to_response(fir: FIR, station_name: str = None, district: str = None, lat: float = None, lng: float = None) -> FIRResponse:
    return FIRResponse(
        id=fir.id, fir_number=fir.fir_number, station_id=fir.station_id,
        crime_type=fir.crime_type.value, status=fir.status.value, priority=fir.priority.value,
        title=fir.title, description=fir.description, incident_date=fir.incident_date,
        registered_date=fir.registered_date, location_id=fir.location_id,
        investigating_officer_id=fir.investigating_officer_id, ipc_sections=fir.ipc_sections,
        summary=fir.summary, is_solved=fir.is_solved, solved_date=fir.solved_date,
        created_at=fir.created_at, station_name=station_name, district=district,
        latitude=lat, longitude=lng,
    )


@router.get("", response_model=PaginatedResponse)
async def list_firs(
    crime_type: Optional[str] = None, status: Optional[str] = None,
    priority: Optional[str] = None, district: Optional[str] = None,
    search: Optional[str] = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    query = select(FIR, PoliceStation.name, PoliceStation.district, Location.latitude, Location.longitude).join(
        PoliceStation, FIR.station_id == PoliceStation.id
    ).outerjoin(Location, FIR.location_id == Location.id)

    filters = []
    if crime_type:
        filters.append(FIR.crime_type == CrimeType(crime_type))
    if status:
        filters.append(FIR.status == FIRStatus(status))
    if priority:
        filters.append(FIR.priority == FIRPriority(priority))
    if district:
        filters.append(PoliceStation.district.ilike(f"%{district}%"))
    if search:
        filters.append(or_(FIR.fir_number.ilike(f"%{search}%"), FIR.title.ilike(f"%{search}%"), FIR.description.ilike(f"%{search}%")))
    if filters:
        query = query.where(and_(*filters))

    count_q = select(func.count()).select_from(query.subquery())
    total = (await db.execute(count_q)).scalar() or 0

    query = query.order_by(FIR.incident_date.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(query)).all()

    items = [await _fir_to_response(f, sn, d, float(lat) if lat else None, float(lng) if lng else None) for f, sn, d, lat, lng in rows]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=max(1, (total + page_size - 1) // page_size))


@router.get("/{fir_id}", response_model=FIRDetailResponse)
async def get_fir(fir_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(FIR, PoliceStation.name, PoliceStation.district, Location.latitude, Location.longitude)
        .join(PoliceStation).outerjoin(Location, FIR.location_id == Location.id)
        .where(FIR.id == fir_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="FIR not found")

    fir, sn, d, lat, lng = row
    base = await _fir_to_response(fir, sn, d, float(lat) if lat else None, float(lng) if lng else None)

    ev_result = await db.execute(select(Evidence).where(Evidence.fir_id == fir_id))
    evidence = [EvidenceResponse(id=e.id, evidence_type=e.evidence_type.value, description=e.description, collected_date=e.collected_date, is_verified=e.is_verified) for e in ev_result.scalars()]

    cr_result = await db.execute(
        select(Criminal, FIRCriminal.role).join(FIRCriminal).where(FIRCriminal.fir_id == fir_id)
    )
    criminals = [CriminalBrief(id=c.id, name=c.name, alias=c.alias, risk_score=c.risk_score, is_repeat_offender=c.is_repeat_offender, role=role) for c, role in cr_result.all()]

    vic_result = await db.execute(
        select(Victim).join(FIRVictim).where(FIRVictim.fir_id == fir_id)
    )
    victims = [VictimBrief(id=v.id, name=v.name, age=v.age, gender=v.gender) for v in vic_result.scalars()]

    timeline = [
        {"date": fir.registered_date.isoformat(), "event": "FIR Registered"},
        {"date": fir.incident_date.isoformat(), "event": "Incident Occurred"},
    ]
    if fir.is_solved and fir.solved_date:
        timeline.append({"date": fir.solved_date.isoformat(), "event": "Case Solved"})
    timeline.sort(key=lambda x: x["date"])

    return FIRDetailResponse(**base.model_dump(), evidence=evidence, criminals=criminals, victims=victims, timeline=timeline)


@router.post("", response_model=FIRResponse)
async def create_fir(data: FIRCreate, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("write:fir"))):
    fir = FIR(
        fir_number=data.fir_number, station_id=data.station_id,
        crime_type=CrimeType(data.crime_type), status=FIRStatus(data.status),
        priority=FIRPriority(data.priority), title=data.title, description=data.description,
        incident_date=data.incident_date, location_id=data.location_id,
        investigating_officer_id=data.investigating_officer_id or user.id,
        ipc_sections=data.ipc_sections, summary=data.summary,
    )
    db.add(fir)
    await db.flush()
    await log_audit(db, str(user.id), "create_fir", "fir", str(fir.id))
    return await _fir_to_response(fir)


@router.patch("/{fir_id}", response_model=FIRResponse)
async def update_fir(fir_id: UUID, data: FIRUpdate, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("write:fir"))):
    result = await db.execute(select(FIR).where(FIR.id == fir_id))
    fir = result.scalar_one_or_none()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")

    update_data = data.model_dump(exclude_unset=True)
    for key, val in update_data.items():
        if key in ("status", "priority") and val:
            setattr(fir, key, FIRStatus(val) if key == "status" else FIRPriority(val))
        else:
            setattr(fir, key, val)
    if data.is_solved and not fir.solved_date:
        fir.solved_date = datetime.utcnow()

    await log_audit(db, str(user.id), "update_fir", "fir", str(fir_id))
    return await _fir_to_response(fir)


@router.delete("/{fir_id}")
async def delete_fir(fir_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("write:fir"))):
    result = await db.execute(select(FIR).where(FIR.id == fir_id))
    fir = result.scalar_one_or_none()
    if not fir:
        raise HTTPException(status_code=404, detail="FIR not found")
    await db.delete(fir)
    await log_audit(db, str(user.id), "delete_fir", "fir", str(fir_id))
    return {"message": "FIR deleted"}
