# SurakshAI — Zoho Catalyst Deployment

## Architecture on Catalyst

```
┌─────────────────┐     ┌──────────────────┐     ┌─────────────────┐
│  Catalyst       │     │  Catalyst        │     │  External DBs   │
│  Client (Next)  │────▶│  AppSail/API     │────▶│  PostgreSQL     │
│  Static Hosting │     │  (FastAPI)       │     │  Neo4j Aura     │
└─────────────────┘     └──────────────────┘     │  ChromaDB       │
                                                  └─────────────────┘
```

## Prerequisites

1. Zoho Catalyst account with a project created
2. Catalyst CLI installed: `npm install -g zcatalyst-cli`
3. External PostgreSQL (Catalyst Data Store or cloud PostgreSQL)
4. Neo4j Aura DB (free tier) for graph features
5. ChromaDB hosted instance or self-managed
6. Groq API key

## Backend Deployment (AppSail)

1. Copy `deployment/catalyst/app-config.json` to your Catalyst project
2. Set environment variables in Catalyst console:

```
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/surakshai
NEO4J_URI=bolt://your-neo4j-host:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your-password
CHROMA_HOST=your-chroma-host
CHROMA_PORT=8000
GROQ_API_KEY=your-groq-key
SECRET_KEY=generate-a-strong-secret
CORS_ORIGINS=["https://your-app.catalystapps.in"]
```

3. Deploy backend:

```bash
cd backend
catalyst deploy --only appsail
```

## Frontend Deployment (Web Client)

1. Build the Next.js static export or deploy as Catalyst Web Client:

```bash
cd frontend
echo "NEXT_PUBLIC_API_URL=https://your-api.catalystapps.in/api" > .env.production
npm run build
```

2. For static hosting, configure `next.config.ts` with `output: 'export'` if needed
3. Deploy:

```bash
catalyst deploy --only client
```

## Database Setup on Catalyst

Option A: Use Catalyst Cloud Scale (PostgreSQL-compatible)
Option B: Use external managed PostgreSQL (AWS RDS, Supabase, Neon)

Run schema:
```bash
psql $DATABASE_URL -f database/schema.sql
python scripts/generate_data.py
python scripts/index_embeddings.py
python scripts/sync_neo4j.py
```

## Serverless Considerations

- FastAPI runs on Catalyst AppSail (container-based)
- ChromaDB and Neo4j require external hosting (not serverless-native)
- Use connection pooling for PostgreSQL
- Set `SEED_FIRS=1000` for dev; full 100K dataset for production

## catalyst.json

See `deployment/catalyst/catalyst.json` for project configuration template.

## Health Check

After deployment, verify:
```
GET https://your-api.catalystapps.in/api/health
```

## Security Checklist

- [ ] Change default admin password
- [ ] Rotate JWT SECRET_KEY
- [ ] Enable HTTPS only
- [ ] Restrict CORS origins
- [ ] Store secrets in Catalyst environment variables (not in code)
