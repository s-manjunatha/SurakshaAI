"""
Index FIR records into ChromaDB for semantic search.
Run after data generation: python scripts/index_embeddings.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from services.rag.rag_service import rag_service

DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://surakshai:surakshai_secret@localhost:5432/surakshai",
)
BATCH_SIZE = int(os.getenv("EMBED_BATCH_SIZE", "1000"))
MAX_FIRS = int(os.getenv("EMBED_MAX_FIRS", "10000"))


def main():
    print("Indexing FIR embeddings into ChromaDB...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()
    cur.execute("""
        SELECT f.id, f.fir_number, f.crime_type, f.title, f.description, f.status, f.summary, f.ipc_sections, ps.district
        FROM fir f
        JOIN police_stations ps ON f.station_id = ps.id
        LIMIT %s
    """, (MAX_FIRS,))

    count = 0
    while True:
        rows = cur.fetchmany(BATCH_SIZE)
        if not rows:
            break
        for row in rows:
            fir_id, fir_number, crime_type, title, description, status, summary, ipc_sections, district = row
            fir_data = {
                "fir_number": fir_number, "crime_type": crime_type, "title": title,
                "description": description, "status": status, "summary": summary,
                "ipc_sections": ipc_sections or [], "district": district,
            }
            text = rag_service.build_fir_text(fir_data)
            rag_service.add_fir_document(str(fir_id), fir_number, text, {"crime_type": crime_type, "district": district})
            count += 1
        print(f"  Indexed {count} FIRs...")

    cur.close()
    conn.close()
    print(f"Done! Indexed {count} FIR embeddings.")


if __name__ == "__main__":
    main()
