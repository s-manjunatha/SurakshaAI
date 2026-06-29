from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from app.config import get_settings
from app.routers import auth, fir, criminals, analytics, ai, graph, forecast, alerts, financial, reports

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="AI-Powered Crime Intelligence & Investigation Platform",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api")
app.include_router(fir.router, prefix="/api")
app.include_router(criminals.router, prefix="/api")
app.include_router(analytics.router, prefix="/api")
app.include_router(ai.router, prefix="/api")
app.include_router(graph.router, prefix="/api")
app.include_router(forecast.router, prefix="/api")
app.include_router(alerts.router, prefix="/api")
app.include_router(financial.router, prefix="/api")
app.include_router(reports.router, prefix="/api")


@app.get("/api/health")
async def health():
    return {"status": "healthy", "service": settings.APP_NAME, "version": settings.APP_VERSION}


@app.get("/")
async def root():
    return {"message": "SurakshAI API", "docs": "/docs"}
