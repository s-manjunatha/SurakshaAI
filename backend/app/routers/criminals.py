from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from typing import Optional

from app.database import get_db
from app.auth import get_current_user, require_permission
from app.models import User, Criminal, FIRCriminal, FIR, Vehicle, Phone, BankAccount, FIRCriminal as FC
from app.schemas import CriminalResponse, CriminalDetailResponse, PaginatedResponse

router = APIRouter(prefix="/criminals", tags=["Criminal Profiles"])


@router.get("", response_model=PaginatedResponse)
async def list_criminals(
    search: Optional[str] = None, repeat_only: bool = False,
    min_risk: Optional[int] = None, page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    query = select(Criminal)
    if search:
        query = query.where(Criminal.name.ilike(f"%{search}%") | Criminal.alias.ilike(f"%{search}%"))
    if repeat_only:
        query = query.where(Criminal.is_repeat_offender == True)
    if min_risk is not None:
        query = query.where(Criminal.risk_score >= min_risk)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(Criminal.risk_score.desc()).offset((page - 1) * page_size).limit(page_size))
    criminals = result.scalars().all()

    items = [CriminalResponse.model_validate(c) for c in criminals]
    return PaginatedResponse(items=items, total=total, page=page, page_size=page_size, total_pages=max(1, (total + page_size - 1) // page_size))


@router.get("/{criminal_id}", response_model=CriminalDetailResponse)
async def get_criminal(criminal_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(Criminal).where(Criminal.id == criminal_id))
    criminal = result.scalar_one_or_none()
    if not criminal:
        raise HTTPException(status_code=404, detail="Criminal not found")

    fir_count = (await db.execute(
        select(func.count()).select_from(FIRCriminal).where(FIRCriminal.criminal_id == criminal_id)
    )).scalar() or 0

    fir_history = await db.execute(
        select(FIR.fir_number, FIR.crime_type, FIR.incident_date, FIR.status)
        .join(FIRCriminal).where(FIRCriminal.criminal_id == criminal_id)
        .order_by(FIR.incident_date.desc()).limit(20)
    )
    crime_history = [{"fir_number": r[0], "crime_type": r[1].value, "date": r[2].isoformat(), "status": r[3].value} for r in fir_history.all()]

    vehicles = await db.execute(select(Vehicle).where(Vehicle.owner_criminal_id == criminal_id).limit(10))
    phones = await db.execute(select(Phone).where(Phone.owner_criminal_id == criminal_id).limit(10))
    accounts = await db.execute(select(BankAccount).where(BankAccount.owner_criminal_id == criminal_id).limit(10))

    associated = await db.execute(
        select(Criminal.id, Criminal.name, Criminal.risk_score)
        .join(FIRCriminal, FIRCriminal.criminal_id == Criminal.id)
        .where(FIRCriminal.fir_id.in_(
            select(FIRCriminal.fir_id).where(FIRCriminal.criminal_id == criminal_id)
        ))
        .where(Criminal.id != criminal_id)
        .distinct().limit(10)
    )

    base = CriminalResponse.model_validate(criminal)
    return CriminalDetailResponse(
        **base.model_dump(),
        fir_count=fir_count,
        vehicles=[{"registration": v.registration_number, "make": v.make, "model": v.model} for v in vehicles.scalars()],
        phones=[{"number": p.phone_number, "operator": p.operator} for p in phones.scalars()],
        bank_accounts=[{"account": a.account_number, "bank": a.bank_name, "flagged": a.is_flagged} for a in accounts.scalars()],
        associated_persons=[{"id": str(a[0]), "name": a[1], "risk_score": a[2]} for a in associated.all()],
        crime_history=crime_history,
    )
