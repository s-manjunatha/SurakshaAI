# SurakshAI Documentation

## System Overview

SurakshAI is an enterprise crime intelligence platform integrating structured crime data (PostgreSQL), relationship graphs (Neo4j), vector search (ChromaDB), and AI reasoning (Groq).

## Module Documentation

### AI Crime Assistant
- Natural language queries converted to SQL via Groq
- RAG retrieval from ChromaDB for context
- Supports English and Kannada
- Voice input via Groq Whisper, output via browser SpeechSynthesis
- Every response includes confidence score and source citations

### Criminal Network Analysis
- Neo4j stores COMMITTED, VICTIM_OF, CONNECTED_TO, TRANSFERRED relationships
- Cytoscape.js renders interactive graphs
- Fallback to PostgreSQL join queries when Neo4j unavailable

### Crime Forecasting
- Prophet time-series for volume prediction (fallback: moving average)
- sklearn RandomForest for regional risk scoring
- Hotspot prediction based on recent density trends

### PDF Reports
- ReportLab generates structured investigation reports
- Groq generates executive summary and recommendations
- Includes FIR details, evidence, timeline

## Database ERD (Key Relationships)

```
police_stations ──< fir >── fir_criminals >── criminals
                  │
                  ├── fir_victims >── victims
                  ├── evidence
                  └── locations

criminals ──< vehicles, phones, bank_accounts
bank_accounts ──< transactions >── bank_accounts
```

## Security

- JWT tokens with 8-hour expiry
- Role-based permissions enforced on every endpoint
- Audit logs for create/update/delete operations
- SQL injection prevention (parameterized queries, SELECT-only NL-to-SQL)
