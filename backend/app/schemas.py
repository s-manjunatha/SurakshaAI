from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List, Any
from datetime import datetime
from uuid import UUID


# Auth
class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"


class UserResponse(BaseModel):
    id: UUID
    username: str
    email: str
    full_name: str
    role: str
    badge_number: Optional[str] = None
    station_id: Optional[UUID] = None

    class Config:
        from_attributes = True


class UserCreate(BaseModel):
    username: str
    email: EmailStr
    password: str
    full_name: str
    role: str = "officer"
    badge_number: Optional[str] = None
    station_id: Optional[UUID] = None


# FIR
class FIRBase(BaseModel):
    fir_number: str
    station_id: UUID
    crime_type: str
    status: str = "registered"
    priority: str = "medium"
    title: str
    description: str
    incident_date: datetime
    location_id: Optional[UUID] = None
    investigating_officer_id: Optional[UUID] = None
    ipc_sections: Optional[List[str]] = None
    summary: Optional[str] = None


class FIRCreate(FIRBase):
    pass


class FIRUpdate(BaseModel):
    status: Optional[str] = None
    priority: Optional[str] = None
    title: Optional[str] = None
    description: Optional[str] = None
    is_solved: Optional[bool] = None
    summary: Optional[str] = None
    investigating_officer_id: Optional[UUID] = None


class FIRResponse(FIRBase):
    id: UUID
    registered_date: datetime
    is_solved: bool
    solved_date: Optional[datetime] = None
    created_at: datetime
    station_name: Optional[str] = None
    district: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None

    class Config:
        from_attributes = True


class FIRDetailResponse(FIRResponse):
    evidence: List["EvidenceResponse"] = []
    criminals: List["CriminalBrief"] = []
    victims: List["VictimBrief"] = []
    timeline: List[dict] = []


class FIRFilter(BaseModel):
    crime_type: Optional[str] = None
    status: Optional[str] = None
    priority: Optional[str] = None
    district: Optional[str] = None
    station_id: Optional[UUID] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    search: Optional[str] = None
    page: int = 1
    page_size: int = 20


class PaginatedResponse(BaseModel):
    items: List[Any]
    total: int
    page: int
    page_size: int
    total_pages: int


# Criminal
class CriminalBrief(BaseModel):
    id: UUID
    name: str
    alias: Optional[str] = None
    risk_score: int = 0
    is_repeat_offender: bool = False
    role: Optional[str] = None

    class Config:
        from_attributes = True


class CriminalResponse(BaseModel):
    id: UUID
    name: str
    alias: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    address: Optional[str] = None
    district: Optional[str] = None
    risk_score: int = 0
    is_repeat_offender: bool = False
    gang_affiliation: Optional[str] = None
    modus_operandi: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True


class CriminalDetailResponse(CriminalResponse):
    fir_count: int = 0
    vehicles: List[dict] = []
    phones: List[dict] = []
    bank_accounts: List[dict] = []
    associated_persons: List[dict] = []
    crime_history: List[dict] = []


# Victim
class VictimBrief(BaseModel):
    id: UUID
    name: str
    age: Optional[int] = None
    gender: Optional[str] = None

    class Config:
        from_attributes = True


# Evidence
class EvidenceResponse(BaseModel):
    id: UUID
    evidence_type: str
    description: str
    collected_date: datetime
    is_verified: bool

    class Config:
        from_attributes = True


# Analytics
class DashboardStats(BaseModel):
    total_firs: int
    solved_cases: int
    active_investigations: int
    high_priority: int
    last_30_days: int
    repeat_offenders: int
    unread_alerts: int


class CrimeTrendPoint(BaseModel):
    date: str
    count: int
    crime_type: Optional[str] = None


class HotspotPoint(BaseModel):
    latitude: float
    longitude: float
    count: int
    district: str
    crime_type: Optional[str] = None


# AI Chat
class ChatRequest(BaseModel):
    message: str
    session_id: Optional[UUID] = None
    language: str = "en"


class AISource(BaseModel):
    type: str
    id: str
    title: str
    relevance: float


class ChatResponse(BaseModel):
    session_id: UUID
    message: str
    structured_data: Optional[dict] = None
    confidence: float
    sources: List[AISource] = []
    actions: List[dict] = []
    sql_query: Optional[str] = None


# Graph
class GraphNode(BaseModel):
    id: str
    label: str
    type: str
    data: dict = {}


class GraphEdge(BaseModel):
    id: str
    source: str
    target: str
    label: str
    data: dict = {}


class GraphResponse(BaseModel):
    nodes: List[GraphNode]
    edges: List[GraphEdge]


# Similar Cases
class SimilarCase(BaseModel):
    fir_id: UUID
    fir_number: str
    title: str
    crime_type: str
    similarity_score: float
    summary: Optional[str] = None


# Forecast
class ForecastPoint(BaseModel):
    date: str
    predicted_count: float
    lower_bound: float
    upper_bound: float


class RegionRisk(BaseModel):
    district: str
    risk_score: float
    crime_count: int
    trend: str


# Alerts
class AlertResponse(BaseModel):
    id: UUID
    alert_type: str
    severity: str
    title: str
    message: str
    district: Optional[str] = None
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# Financial
class TransactionResponse(BaseModel):
    id: UUID
    amount: float
    transaction_date: datetime
    transaction_type: Optional[str] = None
    is_suspicious: bool
    suspicion_reason: Optional[str] = None
    from_account: Optional[str] = None
    to_account: Optional[str] = None

    class Config:
        from_attributes = True


class MoneyTrailNode(BaseModel):
    id: str
    label: str
    type: str
    amount: float


class MoneyTrailEdge(BaseModel):
    source: str
    target: str
    amount: float
    date: str
