"use client";

import { useEffect, useRef, useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

const nodeColors: Record<string, string> = {
  Criminal: "#ef4444",
  Victim: "#22c55e",
  FIR: "#0891b2",
  Phone: "#a855f7",
  Vehicle: "#f59e0b",
  BankAccount: "#ec4899",
  Location: "#06b6d4",
};

function NetworkGraph({ nodes, edges }: { nodes: { id: string; label: string; type: string }[]; edges: { id: string; source: string; target: string; label: string }[] }) {
  const containerRef = useRef<HTMLDivElement>(null);
  const cyRef = useRef<cytoscape.Core | null>(null);

  useEffect(() => {
    if (!containerRef.current || nodes.length === 0) return;

    const initGraph = async () => {
      const cytoscape = (await import("cytoscape")).default;
      const coseBilkent = (await import("cytoscape-cose-bilkent")).default;
      cytoscape.use(coseBilkent);

      if (cyRef.current) cyRef.current.destroy();

      cyRef.current = cytoscape({
        container: containerRef.current,
        elements: [
          ...nodes.map((n) => ({ data: { id: n.id, label: n.label, type: n.type } })),
          ...edges.map((e) => ({ data: { id: e.id, source: e.source, target: e.target, label: e.label } })),
        ],
        style: [
          {
            selector: "node",
            style: {
              label: "data(label)",
              "background-color": (ele: cytoscape.NodeSingular) => nodeColors[ele.data("type")] || "#64748b",
              color: "#f1f5f9",
              "font-size": "10px",
              "text-valign": "bottom",
              "text-margin-y": 5,
              width: 40,
              height: 40,
            },
          },
          {
            selector: "edge",
            style: {
              label: "data(label)",
              "line-color": "#475569",
              "target-arrow-color": "#475569",
              "target-arrow-shape": "triangle",
              "curve-style": "bezier",
              "font-size": "8px",
              color: "#94a3b8",
            },
          },
        ],
        layout: { name: "cose-bilkent" } as cytoscape.LayoutOptions,
      });
    };

    initGraph();
    return () => { cyRef.current?.destroy(); };
  }, [nodes, edges]);

  return <div ref={containerRef} className="w-full h-[500px] rounded-lg bg-background" />;
}

function NetworkContent() {
  const searchParams = useSearchParams();
  const [criminalId, setCriminalId] = useState(searchParams.get("criminal") || "");
  const [firId, setFirId] = useState(searchParams.get("fir") || "");
  const [nodes, setNodes] = useState<{ id: string; label: string; type: string }[]>([]);
  const [edges, setEdges] = useState<{ id: string; source: string; target: string; label: string }[]>([]);
  const [loading, setLoading] = useState(false);

  const loadGraph = () => {
    setLoading(true);
    const path = firId ? `/graph/fir/${firId}` : criminalId ? `/graph/criminal/${criminalId}` : null;
    if (!path) { setLoading(false); return; }
    api.get<{ nodes: typeof nodes; edges: typeof edges }>(path)
      .then((data) => { setNodes(data.nodes); setEdges(data.edges); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => {
    if (searchParams.get("fir") || searchParams.get("criminal")) loadGraph();
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Criminal Network Analysis</h1>
        <p className="text-muted-foreground">Interactive relationship graph powered by Neo4j</p>
      </div>

      <Card>
        <CardContent className="p-4 flex gap-3 flex-wrap">
          <Input placeholder="Criminal UUID..." value={criminalId} onChange={(e) => setCriminalId(e.target.value)} className="max-w-xs" />
          <Input placeholder="FIR UUID..." value={firId} onChange={(e) => setFirId(e.target.value)} className="max-w-xs" />
          <Button onClick={loadGraph} disabled={loading}>{loading ? "Loading..." : "Load Graph"}</Button>
        </CardContent>
      </Card>

      <div className="flex gap-2 flex-wrap">
        {Object.entries(nodeColors).map(([type, color]) => (
          <Badge key={type} variant="outline" style={{ borderColor: color, color }}>{type}</Badge>
        ))}
      </div>

      <Card>
        <CardHeader><CardTitle>Network Graph ({nodes.length} nodes, {edges.length} edges)</CardTitle></CardHeader>
        <CardContent>
          {nodes.length > 0 ? (
            <NetworkGraph nodes={nodes} edges={edges} />
          ) : (
            <div className="h-[500px] flex items-center justify-center text-muted-foreground">
              Enter a Criminal or FIR ID and click Load Graph
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}

export default function NetworkPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><NetworkContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
