from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from typing import Optional
from datetime import datetime, timedelta

from app.database import get_db
from app.auth import get_current_user
from app.models import User, FIR, Criminal, Alert, PoliceStation, Location, CrimeType
from app.schemas import DashboardStats, CrimeTrendPoint, HotspotPoint, PaginatedResponse, AlertResponse

router = APIRouter(prefix="/analytics", tags=["Analytics & Dashboard"])


@router.get("/dashboard", response_model=DashboardStats)
async def dashboard_stats(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    stats = await db.execute(text("""
        SELECT
            COUNT(*) AS total_firs,
            COUNT(*) FILTER (WHERE is_solved = TRUE) AS solved_cases,
            COUNT(*) FILTER (WHERE status = 'under_investigation') AS active_investigations,
            COUNT(*) FILTER (WHERE priority IN ('high', 'critical')) AS high_priority,
            COUNT(*) FILTER (WHERE registered_date >= NOW() - INTERVAL '30 days') AS last_30_days
        FROM fir
    """))
    row = stats.first()

    repeat = (await db.execute(select(func.count()).select_from(Criminal).where(Criminal.is_repeat_offender == True))).scalar() or 0
    alerts = (await db.execute(select(func.count()).select_from(Alert).where(Alert.is_read == False))).scalar() or 0

    return DashboardStats(
        total_firs=row[0] or 0, solved_cases=row[1] or 0,
        active_investigations=row[2] or 0, high_priority=row[3] or 0,
        last_30_days=row[4] or 0, repeat_offenders=repeat, unread_alerts=alerts,
    )


@router.get("/trends", response_model=list[CrimeTrendPoint])
async def crime_trends(
    days: int = Query(90, ge=7, le=365), crime_type: Optional[str] = None,
    district: Optional[str] = None, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    filters = ["f.incident_date >= NOW() - INTERVAL '%d days'" % days]
    params = {}
    if crime_type:
        filters.append("f.crime_type = :crime_type")
        params["crime_type"] = crime_type
    if district:
        filters.append("ps.district ILIKE :district")
        params["district"] = f"%{district}%"

    where = " AND ".join(filters)
    query = f"""
        SELECT DATE_TRUNC('day', f.incident_date)::date as date, COUNT(*) as count, f.crime_type::text
        FROM fir f JOIN police_stations ps ON f.station_id = ps.id
        WHERE {where}
        GROUP BY DATE_TRUNC('day', f.incident_date), f.crime_type
        ORDER BY date
    """
    result = await db.execute(text(query), params)
    return [CrimeTrendPoint(date=str(r[0]), count=r[1], crime_type=r[2]) for r in result.all()]


@router.get("/crime-types")
async def crime_type_distribution(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(text("SELECT crime_type, COUNT(*) FROM fir GROUP BY crime_type ORDER BY COUNT(*) DESC"))
    return [{"crime_type": r[0], "count": r[1]} for r in result.all()]


@router.get("/demographics")
async def demographics(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    age_result = await db.execute(text("""
        SELECT CASE
            WHEN age < 18 THEN 'Under 18'
            WHEN age BETWEEN 18 AND 25 THEN '18-25'
            WHEN age BETWEEN 26 AND 35 THEN '26-35'
            WHEN age BETWEEN 36 AND 50 THEN '36-50'
            ELSE '50+'
        END as age_group, gender, COUNT(*)
        FROM criminals WHERE age IS NOT NULL
        GROUP BY age_group, gender ORDER BY age_group
    """))
    return [{"age_group": r[0], "gender": r[1], "count": r[2]} for r in age_result.all()]


@router.get("/district-comparison")
async def district_comparison(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT ps.district, COUNT(*) as total,
               COUNT(*) FILTER (WHERE f.is_solved) as solved
        FROM fir f JOIN police_stations ps ON f.station_id = ps.id
        GROUP BY ps.district ORDER BY total DESC LIMIT 20
    """))
    return [{"district": r[0], "total": r[1], "solved": r[2], "solve_rate": round(r[2] / max(r[1], 1) * 100, 1)} for r in result.all()]


@router.get("/seasonal")
async def seasonal_trends(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT EXTRACT(MONTH FROM incident_date) as month, crime_type, COUNT(*)
        FROM fir GROUP BY month, crime_type ORDER BY month
    """))
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    return [{"month": months[int(r[0]) - 1], "crime_type": r[1], "count": r[2]} for r in result.all()]


@router.get("/hotspots", response_model=list[HotspotPoint])
async def hotspots(
    crime_type: Optional[str] = None, district: Optional[str] = None,
    days: int = Query(90, ge=7), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user),
):
    filters = ["f.incident_date >= NOW() - INTERVAL '%d days'" % days, "l.latitude IS NOT NULL"]
    if crime_type:
        filters.append(f"f.crime_type = '{crime_type}'")
    if district:
        filters.append(f"l.district ILIKE '%{district}%'")

    query = f"""
        SELECT l.latitude, l.longitude, COUNT(*) as cnt, l.district, f.crime_type
        FROM fir f JOIN locations l ON f.location_id = l.id
        WHERE {' AND '.join(filters)}
        GROUP BY l.latitude, l.longitude, l.district, f.crime_type
        HAVING COUNT(*) >= 2
        ORDER BY cnt DESC LIMIT 500
    """
    result = await db.execute(text(query))
    return [HotspotPoint(latitude=float(r[0]), longitude=float(r[1]), count=r[2], district=r[3], crime_type=r[4]) for r in result.all()]
