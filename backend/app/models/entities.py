import uuid
from datetime import datetime
from sqlalchemy import Column, String, Boolean, DateTime, Text, Integer, ForeignKey, Enum, Numeric, ARRAY
from sqlalchemy.dialects.postgresql import UUID, JSONB, INET
from sqlalchemy.orm import relationship
import enum

from app.database import Base


class UserRole(str, enum.Enum):
    officer = "officer"
    investigator = "investigator"
    supervisor = "supervisor"
    admin = "admin"


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(100), unique=True, nullable=False)
    email = Column(String(255), unique=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(Enum(UserRole), nullable=False, default=UserRole.officer)
    badge_number = Column(String(50))
    station_id = Column(UUID(as_uuid=True), ForeignKey("police_stations.id"))
    is_active = Column(Boolean, default=True)
    last_login = Column(DateTime(timezone=True))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class CrimeType(str, enum.Enum):
    theft = "theft"
    robbery = "robbery"
    burglary = "burglary"
    assault = "assault"
    murder = "murder"
    kidnapping = "kidnapping"
    fraud = "fraud"
    cyber_crime = "cyber_crime"
    drug_offense = "drug_offense"
    domestic_violence = "domestic_violence"
    vehicle_theft = "vehicle_theft"
    chain_snatching = "chain_snatching"
    rape = "rape"
    dowry_harassment = "dowry_harassment"
    corruption = "corruption"
    money_laundering = "money_laundering"
    extortion = "extortion"
    other = "other"


class FIRStatus(str, enum.Enum):
    registered = "registered"
    under_investigation = "under_investigation"
    charge_sheet_filed = "charge_sheet_filed"
    closed = "closed"
    pending_trial = "pending_trial"
    convicted = "convicted"
    acquitted = "acquitted"


class FIRPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"
    critical = "critical"


class PoliceStation(Base):
    __tablename__ = "police_stations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    code = Column(String(20), unique=True, nullable=False)
    district = Column(String(100), nullable=False)
    state = Column(String(100), default="Karnataka")
    address = Column(Text)
    latitude = Column(Numeric(10, 7))
    longitude = Column(Numeric(10, 7))
    phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Location(Base):
    __tablename__ = "locations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255))
    address = Column(Text)
    district = Column(String(100), nullable=False)
    taluk = Column(String(100))
    pincode = Column(String(10))
    latitude = Column(Numeric(10, 7), nullable=False)
    longitude = Column(Numeric(10, 7), nullable=False)
    location_type = Column(String(50), default="crime_scene")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class FIR(Base):
    __tablename__ = "fir"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fir_number = Column(String(50), unique=True, nullable=False)
    station_id = Column(UUID(as_uuid=True), ForeignKey("police_stations.id"), nullable=False)
    crime_type = Column(Enum(CrimeType), nullable=False)
    status = Column(Enum(FIRStatus), nullable=False, default=FIRStatus.registered)
    priority = Column(Enum(FIRPriority), nullable=False, default=FIRPriority.medium)
    title = Column(String(500), nullable=False)
    description = Column(Text, nullable=False)
    incident_date = Column(DateTime(timezone=True), nullable=False)
    registered_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    location_id = Column(UUID(as_uuid=True), ForeignKey("locations.id"))
    investigating_officer_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    ipc_sections = Column(ARRAY(String))
    summary = Column(Text)
    is_solved = Column(Boolean, default=False)
    solved_date = Column(DateTime(timezone=True))
    embedding_id = Column(String(100))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)

    station = relationship("PoliceStation")
    location = relationship("Location")


class Criminal(Base):
    __tablename__ = "criminals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    alias = Column(String(255))
    age = Column(Integer)
    gender = Column(String(20))
    aadhaar_hash = Column(String(64))
    address = Column(Text)
    district = Column(String(100))
    photo_url = Column(Text)
    risk_score = Column(Integer, default=0)
    is_repeat_offender = Column(Boolean, default=False)
    gang_affiliation = Column(String(255))
    modus_operandi = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class Victim(Base):
    __tablename__ = "victims"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(255), nullable=False)
    age = Column(Integer)
    gender = Column(String(20))
    address = Column(Text)
    district = Column(String(100))
    contact_phone = Column(String(20))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class EvidenceType(str, enum.Enum):
    physical = "physical"
    digital = "digital"
    documentary = "documentary"
    forensic = "forensic"
    witness_statement = "witness_statement"
    cctv = "cctv"
    audio = "audio"
    other = "other"


class Evidence(Base):
    __tablename__ = "evidence"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fir_id = Column(UUID(as_uuid=True), ForeignKey("fir.id", ondelete="CASCADE"), nullable=False)
    evidence_type = Column(Enum(EvidenceType), nullable=False)
    description = Column(Text, nullable=False)
    collected_date = Column(DateTime(timezone=True), default=datetime.utcnow)
    collected_by = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    file_url = Column(Text)
    chain_of_custody = Column(JSONB, default=list)
    is_verified = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Vehicle(Base):
    __tablename__ = "vehicles"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    registration_number = Column(String(20), unique=True, nullable=False)
    make = Column(String(100))
    model = Column(String(100))
    color = Column(String(50))
    vehicle_type = Column(String(50))
    owner_criminal_id = Column(UUID(as_uuid=True), ForeignKey("criminals.id"))
    is_stolen = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Phone(Base):
    __tablename__ = "phones"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    phone_number = Column(String(15), unique=True, nullable=False)
    imei = Column(String(20))
    operator = Column(String(50))
    owner_criminal_id = Column(UUID(as_uuid=True), ForeignKey("criminals.id"))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    account_number = Column(String(30), nullable=False)
    ifsc_code = Column(String(15), nullable=False)
    bank_name = Column(String(255), nullable=False)
    account_holder_name = Column(String(255))
    owner_criminal_id = Column(UUID(as_uuid=True), ForeignKey("criminals.id"))
    is_flagged = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Transaction(Base):
    __tablename__ = "transactions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"))
    to_account_id = Column(UUID(as_uuid=True), ForeignKey("bank_accounts.id"))
    amount = Column(Numeric(15, 2), nullable=False)
    transaction_date = Column(DateTime(timezone=True), nullable=False)
    transaction_type = Column(String(50))
    reference_number = Column(String(100))
    is_suspicious = Column(Boolean, default=False)
    suspicion_reason = Column(Text)
    fir_id = Column(UUID(as_uuid=True), ForeignKey("fir.id"))
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class FIRCriminal(Base):
    __tablename__ = "fir_criminals"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fir_id = Column(UUID(as_uuid=True), ForeignKey("fir.id", ondelete="CASCADE"), nullable=False)
    criminal_id = Column(UUID(as_uuid=True), ForeignKey("criminals.id"), nullable=False)
    role = Column(String(50), default="accused")
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class FIRVictim(Base):
    __tablename__ = "fir_victims"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fir_id = Column(UUID(as_uuid=True), ForeignKey("fir.id", ondelete="CASCADE"), nullable=False)
    victim_id = Column(UUID(as_uuid=True), ForeignKey("victims.id"), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class AlertType(str, enum.Enum):
    repeat_offender = "repeat_offender"
    gang_activity = "gang_activity"
    crime_spike = "crime_spike"
    suspicious_transaction = "suspicious_transaction"
    hotspot = "hotspot"
    system = "system"


class AlertSeverity(str, enum.Enum):
    info = "info"
    warning = "warning"
    critical = "critical"


class Alert(Base):
    __tablename__ = "alerts"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    alert_type = Column(Enum(AlertType), nullable=False)
    severity = Column(Enum(AlertSeverity), nullable=False, default=AlertSeverity.info)
    title = Column(String(500), nullable=False)
    message = Column(Text, nullable=False)
    related_fir_id = Column(UUID(as_uuid=True), ForeignKey("fir.id"))
    related_criminal_id = Column(UUID(as_uuid=True), ForeignKey("criminals.id"))
    district = Column(String(100))
    is_read = Column(Boolean, default=False)
    is_resolved = Column(Boolean, default=False)
    alert_metadata = Column("metadata", JSONB)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)


class Investigation(Base):
    __tablename__ = "investigations"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    fir_id = Column(UUID(as_uuid=True), ForeignKey("fir.id"), nullable=False)
    lead_investigator_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))
    status = Column(String(50), default="active")
    notes = Column(Text)
    timeline = Column(JSONB, default=list)
    findings = Column(Text)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatSession(Base):
    __tablename__ = "chat_sessions"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"), nullable=False)
    title = Column(String(255))
    context = Column(JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    updated_at = Column(DateTime(timezone=True), default=datetime.utcnow, onupdate=datetime.utcnow)


class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    session_id = Column(UUID(as_uuid=True), ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(20), nullable=False)
    content = Column(Text, nullable=False)
    message_metadata = Column("metadata", JSONB, default=dict)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
