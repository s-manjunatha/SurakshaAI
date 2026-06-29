import sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from typing import Optional

from app.database import get_db
from app.auth import get_current_user
from app.models import User
from app.schemas import ForecastPoint, RegionRisk

from services.forecasting.forecast_service import forecast_service

router = APIRouter(prefix="/forecast", tags=["Crime Forecasting"])


@router.get("/volume", response_model=list[ForecastPoint])
async def forecast_volume(periods: int = Query(30, ge=7, le=90), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT DATE_TRUNC('day', incident_date)::date as date, COUNT(*) as count
        FROM fir WHERE incident_date >= NOW() - INTERVAL '365 days'
        GROUP BY DATE_TRUNC('day', incident_date) ORDER BY date
    """))
    daily = [{"date": str(r[0]), "count": r[1]} for r in result.all()]
    return forecast_service.forecast_crime_volume(daily, periods)


@router.get("/hotspots")
async def forecast_hotspots(top_n: int = Query(10, ge=5, le=50), db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT l.district, l.latitude, l.longitude, COUNT(*) as count
        FROM fir f JOIN locations l ON f.location_id = l.id
        WHERE f.incident_date >= NOW() - INTERVAL '90 days'
        GROUP BY l.district, l.latitude, l.longitude
    """))
    data = [{"district": r[0], "latitude": float(r[1]), "longitude": float(r[2]), "count": r[3]} for r in result.all()]
    return forecast_service.predict_hotspots(data, top_n)


@router.get("/region-risk", response_model=list[RegionRisk])
async def region_risk(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(text("""
        SELECT ps.district,
               COUNT(*) FILTER (WHERE f.incident_date >= NOW() - INTERVAL '30 days') as recent,
               COUNT(*) FILTER (WHERE f.incident_date >= NOW() - INTERVAL '60 days' AND f.incident_date < NOW() - INTERVAL '30 days') as prev
        FROM fir f JOIN police_stations ps ON f.station_id = ps.id
        GROUP BY ps.district
    """))
    stats = [{"district": r[0], "crime_count": r[1], "prev_count": r[2]} for r in result.all()]
    return forecast_service.region_risk_scores(stats)
