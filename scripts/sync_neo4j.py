"""
Sync PostgreSQL data to Neo4j graph database.
Run after data generation: python scripts/sync_neo4j.py
"""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "backend"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import psycopg2
from services.graph.graph_service import graph_service

DATABASE_URL = os.getenv(
    "DATABASE_URL_SYNC",
    "postgresql://surakshai:surakshai_secret@localhost:5432/surakshai",
)
MAX_RECORDS = int(os.getenv("NEO4J_SYNC_LIMIT", "5000"))


def main():
    print("Syncing data to Neo4j...")
    conn = psycopg2.connect(DATABASE_URL)
    cur = conn.cursor()

    cur.execute("SELECT id, name, risk_score FROM criminals LIMIT %s", (MAX_RECORDS,))
    for row in cur.fetchall():
        graph_service.upsert_criminal(str(row[0]), row[1], row[2] or 0)

    cur.execute("SELECT id, fir_number, crime_type FROM fir LIMIT %s", (MAX_RECORDS,))
    for row in cur.fetchall():
        graph_service.upsert_fir(str(row[0]), row[1], row[2])

    cur.execute("""
        SELECT fc.criminal_id, fc.fir_id FROM fir_criminals fc
        JOIN fir f ON f.id = fc.fir_id LIMIT %s
    """, (MAX_RECORDS,))
    for row in cur.fetchall():
        graph_service.link_committed(str(row[0]), str(row[1]))

    cur.execute("""
        SELECT fv.victim_id, fv.fir_id FROM fir_victims fv LIMIT %s
    """, (MAX_RECORDS,))
    for row in cur.fetchall():
        graph_service.link_victim_of(str(row[0]), str(row[1]))

    cur.close()
    conn.close()
    print("Neo4j sync complete!")


if __name__ == "__main__":
    main()
