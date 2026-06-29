from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, update
from typing import Optional

from app.database import get_db
from app.auth import get_current_user, require_permission
from app.models import User, Alert, AlertType, AlertSeverity
from app.schemas import AlertResponse, PaginatedResponse

router = APIRouter(prefix="/alerts", tags=["Alert System"])


@router.get("", response_model=PaginatedResponse)
async def list_alerts(
    unread_only: bool = False, severity: Optional[str] = None,
    page: int = Query(1, ge=1), page_size: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    query = select(Alert)
    if unread_only:
        query = query.where(Alert.is_read == False)
    if severity:
        query = query.where(Alert.severity == AlertSeverity(severity))

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar() or 0
    result = await db.execute(query.order_by(Alert.created_at.desc()).offset((page - 1) * page_size).limit(page_size))
    alerts = [AlertResponse(id=a.id, alert_type=a.alert_type.value, severity=a.severity.value, title=a.title, message=a.message, district=a.district, is_read=a.is_read, created_at=a.created_at) for a in result.scalars()]

    return PaginatedResponse(items=alerts, total=total, page=page, page_size=page_size, total_pages=max(1, (total + page_size - 1) // page_size))


@router.patch("/{alert_id}/read")
async def mark_read(alert_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    await db.execute(update(Alert).where(Alert.id == alert_id).values(is_read=True))
    return {"message": "Alert marked as read"}


@router.patch("/{alert_id}/resolve")
async def resolve_alert(alert_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("manage:alerts"))):
    await db.execute(update(Alert).where(Alert.id == alert_id).values(is_resolved=True, is_read=True))
    return {"message": "Alert resolved"}


@router.post("/generate")
async def generate_alerts(db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("manage:alerts"))):
    from sqlalchemy import text
    generated = 0

    repeat_offenders = await db.execute(text("""
        SELECT c.id, c.name, COUNT(fc.fir_id) as fir_count
        FROM criminals c JOIN fir_criminals fc ON fc.criminal_id = c.id
        GROUP BY c.id, c.name HAVING COUNT(fc.fir_id) >= 3
        LIMIT 20
    """))
    for row in repeat_offenders.all():
        alert = Alert(
            alert_type=AlertType.repeat_offender, severity=AlertSeverity.warning,
            title=f"Repeat Offender: {row[1]}",
            message=f"Criminal {row[1]} linked to {row[2]} FIRs",
            related_criminal_id=row[0],
        )
        db.add(alert)
        generated += 1

    crime_spikes = await db.execute(text("""
        SELECT ps.district, COUNT(*) as cnt
        FROM fir f JOIN police_stations ps ON f.station_id = ps.id
        WHERE f.incident_date >= NOW() - INTERVAL '7 days'
        GROUP BY ps.district HAVING COUNT(*) > 10
    """))
    for row in crime_spikes.all():
        alert = Alert(
            alert_type=AlertType.crime_spike, severity=AlertSeverity.critical,
            title=f"Crime Spike in {row[0]}",
            message=f"{row[1]} crimes reported in last 7 days in {row[0]}",
            district=row[0],
        )
        db.add(alert)
        generated += 1

    return {"generated": generated}
