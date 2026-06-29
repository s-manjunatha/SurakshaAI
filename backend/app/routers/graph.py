from uuid import UUID
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text

from app.database import get_db
from app.auth import get_current_user
from app.models import User, FIRCriminal, Criminal
from app.schemas import GraphResponse, GraphNode, GraphEdge

from app.services.graph.graph_service import graph_service

router = APIRouter(prefix="/graph", tags=["Network Analysis"])


@router.get("/criminal/{criminal_id}", response_model=GraphResponse)
async def criminal_network(criminal_id: UUID, depth: int = Query(2, ge=1, le=3), user: User = Depends(get_current_user)):
    try:
        data = graph_service.get_criminal_network(str(criminal_id), depth)
        if not data["nodes"]:
            data = await _build_from_postgres(criminal_id)
        return GraphResponse(
            nodes=[GraphNode(**n) for n in data["nodes"]],
            edges=[GraphEdge(**e) for e in data["edges"]],
        )
    except Exception:
        data = await _build_from_postgres(criminal_id)
        return GraphResponse(
            nodes=[GraphNode(**n) for n in data["nodes"]],
            edges=[GraphEdge(**e) for e in data["edges"]],
        )


async def _build_from_postgres(criminal_id: UUID):
    from app.database import AsyncSessionLocal
    async with AsyncSessionLocal() as db:
        result = await db.execute(text("""
            SELECT c.id, c.name, c.risk_score, f.id as fir_id, f.fir_number, f.crime_type
            FROM criminals c
            LEFT JOIN fir_criminals fc ON fc.criminal_id = c.id
            LEFT JOIN fir f ON f.id = fc.fir_id
            WHERE c.id = :cid OR fc.fir_id IN (SELECT fir_id FROM fir_criminals WHERE criminal_id = :cid)
        """), {"cid": str(criminal_id)})

        nodes = {}
        edges = []
        for row in result.all():
            cid, name, risk, fir_id, fir_num, crime = row
            if cid and str(cid) not in nodes:
                nodes[str(cid)] = {"id": str(cid), "label": name, "type": "Criminal", "data": {"risk_score": risk}}
            if fir_id and str(fir_id) not in nodes:
                nodes[str(fir_id)] = {"id": str(fir_id), "label": fir_num, "type": "FIR", "data": {"crime_type": crime}}
                edges.append({"id": f"{cid}-{fir_id}", "source": str(cid), "target": str(fir_id), "label": "COMMITTED", "data": {}})

        return {"nodes": list(nodes.values()), "edges": edges}


@router.get("/fir/{fir_id}", response_model=GraphResponse)
async def fir_network(fir_id: UUID, user: User = Depends(get_current_user)):
    try:
        data = graph_service.get_fir_network(str(fir_id))
    except Exception:
        data = {"nodes": [], "edges": []}
    return GraphResponse(
        nodes=[GraphNode(**n) for n in data["nodes"]],
        edges=[GraphEdge(**e) for e in data["edges"]],
    )


@router.get("/money-trail/{account_id}")
async def money_trail(account_id: UUID, depth: int = Query(3, ge=1, le=5), user: User = Depends(get_current_user)):
    try:
        return graph_service.get_money_trail(str(account_id), depth)
    except Exception:
        from app.database import AsyncSessionLocal
        async with AsyncSessionLocal() as db:
            result = await db.execute(text("""
                SELECT t.id, t.amount, t.transaction_date, t.is_suspicious,
                       fa.account_number as from_acc, ta.account_number as to_acc
                FROM transactions t
                LEFT JOIN bank_accounts fa ON t.from_account_id = fa.id
                LEFT JOIN bank_accounts ta ON t.to_account_id = ta.id
                WHERE t.from_account_id = :aid OR t.to_account_id = :aid
                ORDER BY t.transaction_date DESC LIMIT 50
            """), {"aid": str(account_id)})
            nodes = {}
            edges = []
            aid = str(account_id)
            nodes[aid] = {"id": aid, "label": aid[:8], "type": "BankAccount", "amount": 0}
            for row in result.all():
                tid, amount, date, suspicious, from_acc, to_acc = row
                edges.append({"source": aid, "target": str(tid), "amount": float(amount), "date": date.isoformat()})
            return {"nodes": list(nodes.values()), "edges": edges}
