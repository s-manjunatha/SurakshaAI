# SurakshAI — AI-Powered Crime Intelligence & Investigation Platform

Enterprise-grade crime analysis, investigation support, and predictive policing intelligence for law enforcement.

![Stack](https://img.shields.io/badge/Next.js-15-black) ![FastAPI](https://img.shields.io/badge/FastAPI-Python-green) ![PostgreSQL](https://img.shields.io/badge/PostgreSQL-16-blue) ![Neo4j](https://img.shields.io/badge/Neo4j-5-green) ![Groq](https://img.shields.io/badge/Groq-LLM-orange)

## Features

| Module | Description |
|--------|-------------|
| **Dashboard** | Crime stats, trends, hotspots, live alerts |
| **AI Assistant** | RAG-powered chat (English + Kannada), voice I/O, evidence citations |
| **FIR Management** | Full CRUD, filtering, timeline, linked entities |
| **Criminal Profiles** | Risk scoring, repeat offender detection, asset links |
| **Network Analysis** | Cytoscape.js graph visualization via Neo4j |
| **Crime Heatmap** | Leaflet + OpenStreetMap density clustering |
| **Analytics** | ECharts time-series, demographics, seasonal trends |
| **Forecasting** | Prophet/sklearn crime volume & hotspot prediction |
| **Similar Cases** | ChromaDB semantic FIR search |
| **Financial Crime** | Transaction tracking, suspicious pattern detection |
| **Alerts** | Repeat offender, gang activity, crime spike alerts |
| **PDF Reports** | AI-generated investigation reports |

## Architecture

```
frontend/          Next.js 15 + Tailwind + shadcn/ui
backend/           FastAPI + JWT RBAC
services/          Groq AI, RAG, Graph, Forecasting, PDF
database/          PostgreSQL schema + Neo4j init
scripts/           Data generation + embedding index
deployment/        Zoho Catalyst configuration
```

## Quick Start

### 1. Start Infrastructure

```bash
docker compose up -d
```

This starts PostgreSQL (5432), Neo4j (7474/7687), and ChromaDB (8001).

### 2. Backend Setup

```bash
cd backend
python -m venv venv
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

pip install -r requirements.txt
cp .env.example .env
# Edit .env — add your GROQ_API_KEY
```

### 3. Generate Data

```bash
cd scripts
pip install -r requirements.txt

# Quick dev dataset (1000 FIRs):
set SEED_FIRS=1000
python generate_data.py

# Full production dataset (100K FIRs):
set SEED_FIRS=100000
set SEED_CRIMINALS=20000
set SEED_VICTIMS=50000
python generate_data.py

# Index embeddings & sync graph
python index_embeddings.py
python sync_neo4j.py
```

### 4. Start Backend

```bash
cd backend
uvicorn app.main:app --reload --port 8000
```

API docs: http://localhost:8000/docs

### 5. Start Frontend

```bash
cd frontend
cp .env.local.example .env.local
npm install
npm run dev
```

App: http://localhost:3000

## Default Credentials

| Role | Username | Password |
|------|----------|----------|
| Admin | admin | Admin@123 |
| Investigator | investigator1 | Investigator@123 |
| Officer | officer1 | Officer@123 |
| Supervisor | supervisor1 | Supervisor@123 |

## Environment Variables

### Backend (`backend/.env`)

| Variable | Description |
|----------|-------------|
| `GROQ_API_KEY` | Groq API key for LLM + Whisper |
| `DATABASE_URL` | PostgreSQL async connection |
| `NEO4J_URI` | Neo4j bolt URI |
| `CHROMA_HOST` | ChromaDB host |
| `SECRET_KEY` | JWT signing secret |

### Frontend (`frontend/.env.local`)

| Variable | Description |
|----------|-------------|
| `NEXT_PUBLIC_API_URL` | Backend API URL |

## API Overview

| Endpoint | Description |
|----------|-------------|
| `POST /api/auth/login` | JWT authentication |
| `GET /api/analytics/dashboard` | Dashboard statistics |
| `GET /api/fir` | List/search FIRs |
| `POST /api/ai/chat` | AI assistant with RAG |
| `GET /api/graph/criminal/{id}` | Network graph data |
| `GET /api/analytics/hotspots` | Map hotspot data |
| `GET /api/forecast/volume` | Crime forecasting |
| `POST /api/ai/similar-cases` | Vector similarity search |
| `GET /api/reports/fir/{id}/pdf` | PDF report download |

## RBAC Roles

- **Officer**: Read FIRs, analytics, AI assistant
- **Investigator**: + Write FIRs, criminals, financial data
- **Supervisor**: + Manage alerts, audit logs
- **Admin**: Full access

## Deployment (Zoho Catalyst)

See [deployment/catalyst/README.md](deployment/catalyst/README.md) for full Catalyst deployment instructions.

## Data Schema

- **PostgreSQL**: 13 tables (users, fir, criminals, victims, evidence, etc.)
- **Neo4j**: Criminal, Victim, FIR, Phone, Vehicle, BankAccount, Location nodes
- **ChromaDB**: FIR embedding vectors for semantic search

## Tech Stack

- **Frontend**: Next.js 15, React, TypeScript, Tailwind CSS, shadcn/ui, Framer Motion, Lucide
- **Backend**: FastAPI, SQLAlchemy, JWT
- **Databases**: PostgreSQL, Neo4j, ChromaDB
- **AI**: Groq API (Llama 3.3 70B), Groq Whisper
- **Visualization**: Apache ECharts, Cytoscape.js, Leaflet
- **ML**: Prophet, scikit-learn

## License

For authorized law enforcement and research use only.
