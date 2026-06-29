-- SurakshAI PostgreSQL Schema
-- Enterprise Crime Intelligence Platform

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";

-- ============================================================
-- USERS & AUTH
-- ============================================================
CREATE TYPE user_role AS ENUM ('officer', 'investigator', 'supervisor', 'admin');

CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(100) UNIQUE NOT NULL,
    email VARCHAR(255) UNIQUE NOT NULL,
    password_hash VARCHAR(255) NOT NULL,
    full_name VARCHAR(255) NOT NULL,
    role user_role NOT NULL DEFAULT 'officer',
    badge_number VARCHAR(50),
    station_id UUID,
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource_type VARCHAR(100),
    resource_id VARCHAR(100),
    details JSONB,
    ip_address INET,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- POLICE STATIONS & LOCATIONS
-- ============================================================
CREATE TABLE police_stations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    code VARCHAR(20) UNIQUE NOT NULL,
    district VARCHAR(100) NOT NULL,
    state VARCHAR(100) DEFAULT 'Karnataka',
    address TEXT,
    latitude DECIMAL(10, 7),
    longitude DECIMAL(10, 7),
    phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

ALTER TABLE users ADD CONSTRAINT fk_users_station
    FOREIGN KEY (station_id) REFERENCES police_stations(id);

CREATE TABLE locations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255),
    address TEXT,
    district VARCHAR(100) NOT NULL,
    taluk VARCHAR(100),
    pincode VARCHAR(10),
    latitude DECIMAL(10, 7) NOT NULL,
    longitude DECIMAL(10, 7) NOT NULL,
    location_type VARCHAR(50) DEFAULT 'crime_scene',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_locations_district ON locations(district);
CREATE INDEX idx_locations_coords ON locations(latitude, longitude);

-- ============================================================
-- FIR MANAGEMENT
-- ============================================================
CREATE TYPE fir_status AS ENUM ('registered', 'under_investigation', 'charge_sheet_filed', 'closed', 'pending_trial', 'convicted', 'acquitted');
CREATE TYPE fir_priority AS ENUM ('low', 'medium', 'high', 'critical');
CREATE TYPE crime_type AS ENUM (
    'theft', 'robbery', 'burglary', 'assault', 'murder', 'kidnapping',
    'fraud', 'cyber_crime', 'drug_offense', 'domestic_violence',
    'vehicle_theft', 'chain_snatching', 'rape', 'dowry_harassment',
    'corruption', 'money_laundering', 'extortion', 'other'
);

CREATE TABLE fir (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fir_number VARCHAR(50) UNIQUE NOT NULL,
    station_id UUID NOT NULL REFERENCES police_stations(id),
    crime_type crime_type NOT NULL,
    status fir_status NOT NULL DEFAULT 'registered',
    priority fir_priority NOT NULL DEFAULT 'medium',
    title VARCHAR(500) NOT NULL,
    description TEXT NOT NULL,
    incident_date TIMESTAMPTZ NOT NULL,
    registered_date TIMESTAMPTZ DEFAULT NOW(),
    location_id UUID REFERENCES locations(id),
    investigating_officer_id UUID REFERENCES users(id),
    ipc_sections TEXT[],
    summary TEXT,
    is_solved BOOLEAN DEFAULT FALSE,
    solved_date TIMESTAMPTZ,
    embedding_id VARCHAR(100),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_fir_crime_type ON fir(crime_type);
CREATE INDEX idx_fir_status ON fir(status);
CREATE INDEX idx_fir_priority ON fir(priority);
CREATE INDEX idx_fir_incident_date ON fir(incident_date);
CREATE INDEX idx_fir_station ON fir(station_id);
CREATE INDEX idx_fir_number_trgm ON fir USING gin(fir_number gin_trgm_ops);

-- ============================================================
-- PERSONS
-- ============================================================
CREATE TABLE criminals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    alias VARCHAR(255),
    age INTEGER,
    gender VARCHAR(20),
    aadhaar_hash VARCHAR(64),
    address TEXT,
    district VARCHAR(100),
    photo_url TEXT,
    risk_score INTEGER DEFAULT 0 CHECK (risk_score >= 0 AND risk_score <= 100),
    is_repeat_offender BOOLEAN DEFAULT FALSE,
    gang_affiliation VARCHAR(255),
    modus_operandi TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_criminals_risk ON criminals(risk_score DESC);
CREATE INDEX idx_criminals_repeat ON criminals(is_repeat_offender) WHERE is_repeat_offender = TRUE;

CREATE TABLE victims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(255) NOT NULL,
    age INTEGER,
    gender VARCHAR(20),
    address TEXT,
    district VARCHAR(100),
    contact_phone VARCHAR(20),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- FIR RELATIONSHIPS
-- ============================================================
CREATE TABLE fir_criminals (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fir_id UUID NOT NULL REFERENCES fir(id) ON DELETE CASCADE,
    criminal_id UUID NOT NULL REFERENCES criminals(id),
    role VARCHAR(50) DEFAULT 'accused',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fir_id, criminal_id)
);

CREATE TABLE fir_victims (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fir_id UUID NOT NULL REFERENCES fir(id) ON DELETE CASCADE,
    victim_id UUID NOT NULL REFERENCES victims(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(fir_id, victim_id)
);

-- ============================================================
-- EVIDENCE
-- ============================================================
CREATE TYPE evidence_type AS ENUM ('physical', 'digital', 'documentary', 'forensic', 'witness_statement', 'cctv', 'audio', 'other');

CREATE TABLE evidence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fir_id UUID NOT NULL REFERENCES fir(id) ON DELETE CASCADE,
    evidence_type evidence_type NOT NULL,
    description TEXT NOT NULL,
    collected_date TIMESTAMPTZ DEFAULT NOW(),
    collected_by UUID REFERENCES users(id),
    file_url TEXT,
    chain_of_custody JSONB DEFAULT '[]',
    is_verified BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- ASSETS: VEHICLES, PHONES, BANK ACCOUNTS
-- ============================================================
CREATE TABLE vehicles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    registration_number VARCHAR(20) UNIQUE NOT NULL,
    make VARCHAR(100),
    model VARCHAR(100),
    color VARCHAR(50),
    vehicle_type VARCHAR(50),
    owner_criminal_id UUID REFERENCES criminals(id),
    is_stolen BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE phones (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    phone_number VARCHAR(15) UNIQUE NOT NULL,
    imei VARCHAR(20),
    operator VARCHAR(50),
    owner_criminal_id UUID REFERENCES criminals(id),
    is_active BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE bank_accounts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    account_number VARCHAR(30) NOT NULL,
    ifsc_code VARCHAR(15) NOT NULL,
    bank_name VARCHAR(255) NOT NULL,
    account_holder_name VARCHAR(255),
    owner_criminal_id UUID REFERENCES criminals(id),
    is_flagged BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(account_number, ifsc_code)
);

CREATE TABLE transactions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    from_account_id UUID REFERENCES bank_accounts(id),
    to_account_id UUID REFERENCES bank_accounts(id),
    amount DECIMAL(15, 2) NOT NULL,
    transaction_date TIMESTAMPTZ NOT NULL,
    transaction_type VARCHAR(50),
    reference_number VARCHAR(100),
    is_suspicious BOOLEAN DEFAULT FALSE,
    suspicion_reason TEXT,
    fir_id UUID REFERENCES fir(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_transactions_date ON transactions(transaction_date);
CREATE INDEX idx_transactions_suspicious ON transactions(is_suspicious) WHERE is_suspicious = TRUE;

-- Criminal asset links
CREATE TABLE criminal_vehicles (
    criminal_id UUID REFERENCES criminals(id) ON DELETE CASCADE,
    vehicle_id UUID REFERENCES vehicles(id) ON DELETE CASCADE,
    relationship VARCHAR(50) DEFAULT 'owns',
    PRIMARY KEY (criminal_id, vehicle_id)
);

CREATE TABLE criminal_phones (
    criminal_id UUID REFERENCES criminals(id) ON DELETE CASCADE,
    phone_id UUID REFERENCES phones(id) ON DELETE CASCADE,
    relationship VARCHAR(50) DEFAULT 'uses',
    PRIMARY KEY (criminal_id, phone_id)
);

CREATE TABLE criminal_bank_accounts (
    criminal_id UUID REFERENCES criminals(id) ON DELETE CASCADE,
    bank_account_id UUID REFERENCES bank_accounts(id) ON DELETE CASCADE,
    relationship VARCHAR(50) DEFAULT 'owns',
    PRIMARY KEY (criminal_id, bank_account_id)
);

-- ============================================================
-- INVESTIGATIONS & ALERTS
-- ============================================================
CREATE TABLE investigations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    fir_id UUID NOT NULL REFERENCES fir(id),
    lead_investigator_id UUID REFERENCES users(id),
    status VARCHAR(50) DEFAULT 'active',
    notes TEXT,
    timeline JSONB DEFAULT '[]',
    findings TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TYPE alert_severity AS ENUM ('info', 'warning', 'critical');
CREATE TYPE alert_type AS ENUM ('repeat_offender', 'gang_activity', 'crime_spike', 'suspicious_transaction', 'hotspot', 'system');

CREATE TABLE alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    alert_type alert_type NOT NULL,
    severity alert_severity NOT NULL DEFAULT 'info',
    title VARCHAR(500) NOT NULL,
    message TEXT NOT NULL,
    related_fir_id UUID REFERENCES fir(id),
    related_criminal_id UUID REFERENCES criminals(id),
    district VARCHAR(100),
    is_read BOOLEAN DEFAULT FALSE,
    is_resolved BOOLEAN DEFAULT FALSE,
    metadata JSONB,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_alerts_unread ON alerts(is_read) WHERE is_read = FALSE;

-- ============================================================
-- CHAT SESSIONS (AI Assistant Memory)
-- ============================================================
CREATE TABLE chat_sessions (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID NOT NULL REFERENCES users(id),
    title VARCHAR(255),
    context JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE chat_messages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    session_id UUID NOT NULL REFERENCES chat_sessions(id) ON DELETE CASCADE,
    role VARCHAR(20) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- ============================================================
-- SEED DEFAULT ADMIN USER (password: Admin@123)
-- bcrypt hash for Admin@123
-- ============================================================
INSERT INTO police_stations (id, name, code, district, latitude, longitude, address)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'Bengaluru City Central Police Station',
    'BLR-CENTRAL',
    'Bengaluru Urban',
    12.9716, 77.5946,
    'MG Road, Bengaluru, Karnataka 560001'
);

INSERT INTO users (id, username, email, password_hash, full_name, role, badge_number, station_id)
VALUES (
    '00000000-0000-0000-0000-000000000001',
    'admin',
    'admin@surakshai.gov.in',
    '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/X4.VTtYqJqZqZqZqO',
    'System Administrator',
    'admin',
    'ADMIN-001',
    '00000000-0000-0000-0000-000000000001'
);

-- Views for analytics
CREATE OR REPLACE VIEW v_crime_stats AS
SELECT
    COUNT(*) AS total_firs,
    COUNT(*) FILTER (WHERE is_solved = TRUE) AS solved_cases,
    COUNT(*) FILTER (WHERE status = 'under_investigation') AS active_investigations,
    COUNT(*) FILTER (WHERE priority IN ('high', 'critical')) AS high_priority,
    COUNT(*) FILTER (WHERE registered_date >= NOW() - INTERVAL '30 days') AS last_30_days
FROM fir;

CREATE OR REPLACE VIEW v_district_crime AS
SELECT
    ps.district,
    f.crime_type,
    COUNT(*) AS crime_count,
    DATE_TRUNC('month', f.incident_date) AS month
FROM fir f
JOIN police_stations ps ON f.station_id = ps.id
GROUP BY ps.district, f.crime_type, DATE_TRUNC('month', f.incident_date);
