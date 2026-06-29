import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, text
import json

from app.database import get_db
from app.auth import get_current_user, require_permission
from app.models import User, FIR, ChatSession, ChatMessage, PoliceStation, Location
from app.schemas import ChatRequest, ChatResponse, AISource, SimilarCase

from services.ai.groq_service import groq_service
from services.rag.rag_service import rag_service

router = APIRouter(prefix="/ai", tags=["AI Assistant"])

SCHEMA_CONTEXT = """
fir(id, fir_number, station_id, crime_type, status, priority, title, description, incident_date, is_solved)
police_stations(id, name, code, district)
criminals(id, name, alias, risk_score, is_repeat_offender, district)
victims(id, name, age, gender)
locations(id, district, latitude, longitude)
fir_criminals(fir_id, criminal_id, role)
"""


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest, db: AsyncSession = Depends(get_db), user: User = Depends(require_permission("use:ai"))):
    session = None
    if request.session_id:
        result = await db.execute(select(ChatSession).where(ChatSession.id == request.session_id, ChatSession.user_id == user.id))
        session = result.scalar_one_or_none()
    if not session:
        session = ChatSession(user_id=user.id, title=request.message[:50])
        db.add(session)
        await db.flush()

    history_result = await db.execute(
        select(ChatMessage).where(ChatMessage.session_id == session.id).order_by(ChatMessage.created_at.desc()).limit(10)
    )
    history = [{"role": m.role, "content": m.content} for m in reversed(history_result.scalars().all())]

    db.add(ChatMessage(session_id=session.id, role="user", content=request.message))
    sources = []
    context_parts = []

    # RAG search
    similar = rag_service.search_similar(request.message, n_results=5)
    for s in similar:
        sources.append(AISource(type="fir", id=s["fir_id"], title=s["metadata"].get("fir_number", s["fir_id"]), relevance=s["similarity_score"]))
        context_parts.append(s["document"])

    # NL to SQL
    sql_result = await groq_service.nl_to_sql(request.message, SCHEMA_CONTEXT)
    sql_data = []
    if sql_result.get("sql"):
        try:
            result = await db.execute(text(sql_result["sql"]))
            rows = result.fetchall()
            cols = result.keys()
            sql_data = [dict(zip(cols, row)) for row in rows[:20]]
            context_parts.append(f"SQL Results: {json.dumps(sql_data, default=str)}")
        except Exception as e:
            context_parts.append(f"SQL query failed: {str(e)}")

    context = "\n".join(context_parts) if context_parts else "No specific data found."

    ai_response = await groq_service.crime_assistant_response(request.message, context, history)

    answer = ai_response.get("answer", "I couldn't process your request.")
    confidence = ai_response.get("confidence", 0.5)
    actions = ai_response.get("suggested_actions", [])

    if not actions and similar:
        actions = [{"type": "view_fir", "label": "View FIR", "resource_id": similar[0]["fir_id"]}]

    metadata = {
        "confidence": confidence,
        "sources": [s.model_dump() for s in sources],
        "structured_insights": ai_response.get("structured_insights", {}),
        "sql_query": sql_result.get("sql"),
    }
    db.add(ChatMessage(session_id=session.id, role="assistant", content=answer, message_metadata=metadata))

    return ChatResponse(
        session_id=session.id, message=answer, confidence=confidence,
        sources=sources, actions=actions, structured_data=ai_response.get("structured_insights"),
        sql_query=sql_result.get("sql"),
    )


@router.get("/sessions")
async def list_sessions(db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(ChatSession).where(ChatSession.user_id == user.id).order_by(ChatSession.updated_at.desc()).limit(20))
    return [{"id": str(s.id), "title": s.title, "created_at": s.created_at.isoformat()} for s in result.scalars()]


@router.get("/sessions/{session_id}/messages")
async def get_session_messages(session_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(select(ChatMessage).where(ChatMessage.session_id == session_id).order_by(ChatMessage.created_at))
    return [{"role": m.role, "content": m.content, "metadata": m.message_metadata, "created_at": m.created_at.isoformat()} for m in result.scalars()]


@router.post("/similar-cases", response_model=list[SimilarCase])
async def similar_cases(body: dict, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    query = body.get("query", "")
    n = body.get("n", 10)
    if not query:
        raise HTTPException(status_code=400, detail="query is required")
    similar = rag_service.search_similar(query, n_results=n)
    results = []
    for s in similar:
        fir_result = await db.execute(select(FIR).where(FIR.id == s["fir_id"]))
        fir = fir_result.scalar_one_or_none()
        if fir:
            results.append(SimilarCase(
                fir_id=fir.id, fir_number=fir.fir_number, title=fir.title,
                crime_type=fir.crime_type.value, similarity_score=s["similarity_score"], summary=fir.summary,
            ))
    return results


@router.post("/summarize/{fir_id}")
async def summarize_fir(fir_id: UUID, db: AsyncSession = Depends(get_db), user: User = Depends(get_current_user)):
    result = await db.execute(
        select(FIR, PoliceStation.district).join(PoliceStation).where(FIR.id == fir_id)
    )
    row = result.first()
    if not row:
        raise HTTPException(status_code=404, detail="FIR not found")
    fir, district = row
    fir_data = {
        "fir_number": fir.fir_number, "crime_type": fir.crime_type.value,
        "title": fir.title, "description": fir.description, "district": district,
        "status": fir.status.value, "ipc_sections": fir.ipc_sections,
    }
    return await groq_service.summarize_case(fir_data)


@router.post("/transcribe")
async def transcribe_audio(audio: UploadFile = File(...), user: User = Depends(get_current_user)):
    content = await audio.read()
    text = await groq_service.transcribe_audio(content, audio.filename or "audio.webm")
    return {"text": text}
