"""Neo4j graph database service for criminal network analysis."""
from neo4j import GraphDatabase
from typing import List, Optional
from app.config import get_settings

settings = get_settings()


class GraphService:
    def __init__(self):
        self._driver = None

    @property
    def driver(self):
        if self._driver is None:
            self._driver = GraphDatabase.driver(
                settings.NEO4J_URI,
                auth=(settings.NEO4J_USER, settings.NEO4J_PASSWORD),
            )
        return self._driver

    def close(self):
        if self._driver:
            self._driver.close()

    def run_query(self, query: str, params: dict = None):
        with self.driver.session() as session:
            result = session.run(query, params or {})
            return [record.data() for record in result]

    def upsert_criminal(self, criminal_id: str, name: str, risk_score: int = 0, **props):
        self.run_query(
            "MERGE (c:Criminal {id: $id}) SET c.name = $name, c.risk_score = $risk_score, c += $props",
            {"id": criminal_id, "name": name, "risk_score": risk_score, "props": props},
        )

    def upsert_fir(self, fir_id: str, fir_number: str, crime_type: str, **props):
        self.run_query(
            "MERGE (f:FIR {id: $id}) SET f.fir_number = $fir_number, f.crime_type = $crime_type, f += $props",
            {"id": fir_id, "fir_number": fir_number, "crime_type": crime_type, "props": props},
        )

    def link_committed(self, criminal_id: str, fir_id: str):
        self.run_query(
            "MATCH (c:Criminal {id: $cid}), (f:FIR {id: $fid}) MERGE (c)-[:COMMITTED]->(f)",
            {"cid": criminal_id, "fid": fir_id},
        )

    def link_victim_of(self, victim_id: str, fir_id: str):
        self.run_query(
            "MATCH (v:Victim {id: $vid}), (f:FIR {id: $fid}) MERGE (v)-[:VICTIM_OF]->(f)",
            {"vid": victim_id, "fid": fir_id},
        )

    def link_connected(self, criminal_id_1: str, criminal_id_2: str, strength: float = 0.5, rel_type: str = "associate"):
        self.run_query(
            """MATCH (c1:Criminal {id: $id1}), (c2:Criminal {id: $id2})
               MERGE (c1)-[r:CONNECTED_TO]->(c2)
               SET r.strength = $strength, r.type = $rel_type""",
            {"id1": criminal_id_1, "id2": criminal_id_2, "strength": strength, "rel_type": rel_type},
        )

    def get_criminal_network(self, criminal_id: str, depth: int = 2) -> dict:
        query = """
        MATCH path = (c:Criminal {id: $cid})-[*1..%d]-(connected)
        RETURN c, connected, relationships(path) as rels
        LIMIT 200
        """ % depth
        records = self.run_query(query, {"cid": criminal_id})
        nodes = {}
        edges = []

        for record in records:
            c = record.get("c")
            connected = record.get("connected")
            if c:
                nodes[c["id"]] = {"id": c["id"], "label": c.get("name", c["id"]), "type": list(c.labels)[0] if hasattr(c, 'labels') else "Criminal", "data": dict(c)}
            if connected:
                labels = list(connected.labels) if hasattr(connected, 'labels') else ["Unknown"]
                node_type = labels[0] if labels else "Unknown"
                label = connected.get("name") or connected.get("fir_number") or connected.get("phone_number") or connected.get("registration_number") or connected["id"]
                nodes[connected["id"]] = {"id": connected["id"], "label": label, "type": node_type, "data": dict(connected)}

        return {"nodes": list(nodes.values()), "edges": edges}

    def get_fir_network(self, fir_id: str) -> dict:
        query = """
        MATCH (f:FIR {id: $fid})
        OPTIONAL MATCH (c:Criminal)-[:COMMITTED]->(f)
        OPTIONAL MATCH (v:Victim)-[:VICTIM_OF]->(f)
        OPTIONAL MATCH (c2:Criminal)-[:USED|OWNS|CONNECTED_TO*1..2]-(c)
        OPTIONAL MATCH (f)-[:OCCURRED_AT]->(l:Location)
        RETURN f, collect(distinct c) as criminals, collect(distinct v) as victims,
               collect(distinct l) as locations
        """
        records = self.run_query(query, {"fid": fir_id})
        nodes = []
        edges = []
        seen = set()

        if records:
            rec = records[0]
            f = rec.get("f")
            if f:
                nodes.append({"id": f["id"], "label": f.get("fir_number", "FIR"), "type": "FIR", "data": dict(f)})
                seen.add(f["id"])

            for c in rec.get("criminals") or []:
                if c and c["id"] not in seen:
                    nodes.append({"id": c["id"], "label": c.get("name", ""), "type": "Criminal", "data": dict(c)})
                    edges.append({"id": f"{c['id']}-{fir_id}", "source": c["id"], "target": fir_id, "label": "COMMITTED", "data": {}})
                    seen.add(c["id"])

            for v in rec.get("victims") or []:
                if v and v["id"] not in seen:
                    nodes.append({"id": v["id"], "label": v.get("name", ""), "type": "Victim", "data": dict(v)})
                    edges.append({"id": f"{v['id']}-{fir_id}", "source": v["id"], "target": fir_id, "label": "VICTIM_OF", "data": {}})
                    seen.add(v["id"])

            for l in rec.get("locations") or []:
                if l and l["id"] not in seen:
                    nodes.append({"id": l["id"], "label": l.get("name", l.get("district", "Location")), "type": "Location", "data": dict(l)})
                    edges.append({"id": f"{fir_id}-{l['id']}", "source": fir_id, "target": l["id"], "label": "OCCURRED_AT", "data": {}})
                    seen.add(l["id"])

        return {"nodes": nodes, "edges": edges}

    def get_money_trail(self, account_id: str, depth: int = 3) -> dict:
        query = """
        MATCH path = (start:BankAccount {id: $aid})-[:TRANSFERRED*1..%d]->(end:BankAccount)
        RETURN start, end, relationships(path) as rels
        LIMIT 100
        """ % depth
        records = self.run_query(query, {"aid": account_id})
        nodes = {}
        edges = []

        for record in records:
            start = record.get("start")
            end = record.get("end")
            if start:
                nodes[start["id"]] = {"id": start["id"], "label": start.get("account_number", ""), "type": "BankAccount", "amount": 0}
            if end:
                nodes[end["id"]] = {"id": end["id"], "label": end.get("account_number", ""), "type": "BankAccount", "amount": 0}
            rels = record.get("rels") or []
            for rel in rels:
                if hasattr(rel, 'start_node') and hasattr(rel, 'end_node'):
                    edges.append({
                        "source": rel.start_node["id"],
                        "target": rel.end_node["id"],
                        "amount": rel.get("amount", 0),
                        "date": str(rel.get("date", "")),
                    })

        return {"nodes": list(nodes.values()), "edges": edges}


graph_service = GraphService()
