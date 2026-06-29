"""Groq AI integration layer for SurakshAI."""
import json
import re
from typing import Optional
from groq import Groq
from app.config import get_settings

settings = get_settings()


class GroqService:
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY) if settings.GROQ_API_KEY else None
        self.model = settings.GROQ_MODEL

    def _ensure_client(self):
        if not self.client:
            raise ValueError("GROQ_API_KEY not configured. Set it in .env file.")

    async def chat_completion(self, messages: list, temperature: float = 0.3, max_tokens: int = 4096) -> str:
        self._ensure_client()
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
        )
        return response.choices[0].message.content

    async def nl_to_sql(self, question: str, schema_context: str) -> dict:
        """Convert natural language to SQL with explanation."""
        system_prompt = f"""You are a PostgreSQL expert for Indian crime database SurakshAI.
Convert the user's question to a safe SELECT query only. Never use INSERT, UPDATE, DELETE, DROP.
Return JSON with keys: sql, explanation, confidence (0-1).

Database schema:
{schema_context}

Rules:
- Only SELECT queries
- Use proper JOINs
- Limit results to 100 rows max
- Handle Kannada questions by translating intent first
"""
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": question},
        ]
        try:
            result = await self.chat_completion(messages, temperature=0.1)
            parsed = self._extract_json(result)
            if parsed and "sql" in parsed:
                sql = parsed["sql"].strip()
                if not sql.upper().startswith("SELECT"):
                    raise ValueError("Only SELECT queries allowed")
                if "LIMIT" not in sql.upper():
                    sql += " LIMIT 100"
                parsed["sql"] = sql
                return parsed
        except Exception:
            pass
        return {"sql": None, "explanation": "Could not generate SQL", "confidence": 0.0}

    async def summarize_case(self, fir_data: dict) -> dict:
        prompt = f"""Summarize this FIR case for investigators. Return JSON with:
summary, key_findings (list), investigation_suggestions (list), confidence (0-1)

FIR Data:
{json.dumps(fir_data, default=str, indent=2)}"""
        messages = [
            {"role": "system", "content": "You are an expert criminal investigator AI assistant for Karnataka Police."},
            {"role": "user", "content": prompt},
        ]
        result = await self.chat_completion(messages)
        return self._extract_json(result) or {"summary": result, "confidence": 0.7}

    async def crime_assistant_response(self, question: str, context: str, history: list = None) -> dict:
        system_prompt = """You are SurakshAI, an AI crime intelligence assistant for Karnataka Police.
Support English and Kannada. Always provide evidence-based answers.
Return JSON with: answer, confidence (0-1), structured_insights (object), suggested_actions (list of {type, label, resource_id}).

Action types: view_fir, view_graph, view_map, generate_pdf, view_criminal"""
        messages = [{"role": "system", "content": system_prompt}]
        if history:
            messages.extend(history[-6:])
        messages.append({"role": "user", "content": f"Context from database:\n{context}\n\nQuestion: {question}"})

        result = await self.chat_completion(messages)
        parsed = self._extract_json(result)
        if parsed:
            return parsed
        return {"answer": result, "confidence": 0.6, "structured_insights": {}, "suggested_actions": []}

    async def translate(self, text: str, target_lang: str = "en") -> str:
        prompt = f"Translate to {target_lang}. Return only the translation:\n{text}"
        return await self.chat_completion([{"role": "user", "content": prompt}], temperature=0.1)

    async def generate_report_content(self, report_data: dict) -> dict:
        prompt = f"""Generate an investigation report. Return JSON with:
executive_summary, findings (list), recommendations (list), risk_assessment

Data:
{json.dumps(report_data, default=str, indent=2)}"""
        result = await self.chat_completion([
            {"role": "system", "content": "You are a senior police report writer."},
            {"role": "user", "content": prompt},
        ])
        return self._extract_json(result) or {"executive_summary": result}

    async def transcribe_audio(self, audio_bytes: bytes, filename: str = "audio.webm") -> str:
        self._ensure_client()
        transcription = self.client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model=settings.GROQ_WHISPER_MODEL,
        )
        return transcription.text

    def _extract_json(self, text: str) -> Optional[dict]:
        try:
            return json.loads(text)
        except json.JSONDecodeError:
            pass
        match = re.search(r'\{[\s\S]*\}', text)
        if match:
            try:
                return json.loads(match.group())
            except json.JSONDecodeError:
                pass
        return None


groq_service = GroqService()
