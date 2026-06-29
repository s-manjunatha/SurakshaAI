"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft, Download, Network, Map } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface FIRDetail {
  id: string;
  fir_number: string;
  crime_type: string;
  status: string;
  priority: string;
  title: string;
  description: string;
  incident_date: string;
  registered_date: string;
  is_solved: boolean;
  district?: string;
  station_name?: string;
  ipc_sections?: string[];
  summary?: string;
  evidence: { id: string; evidence_type: string; description: string; is_verified: boolean }[];
  criminals: { id: string; name: string; risk_score: number; role?: string }[];
  victims: { id: string; name: string; age?: number }[];
  timeline: { date: string; event: string }[];
}

function FIRDetailContent() {
  const params = useParams();
  const [fir, setFir] = useState<FIRDetail | null>(null);

  useEffect(() => {
    if (params.id) {
      api.get<FIRDetail>(`/fir/${params.id}`).then(setFir).catch(console.error);
    }
  }, [params.id]);

  if (!fir) return <div className="text-center py-12 text-muted-foreground">Loading FIR details...</div>;

  const pdfUrl = `${process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api"}/reports/fir/${fir.id}/pdf`;

  return (
    <div className="space-y-6">
      <div className="flex items-start justify-between gap-4 flex-wrap">
        <div>
          <Link href="/fir" className="text-sm text-muted-foreground flex items-center gap-1 mb-2 hover:text-primary">
            <ArrowLeft className="h-4 w-4" /> Back to FIRs
          </Link>
          <h1 className="text-2xl font-bold font-mono">{fir.fir_number}</h1>
          <p className="text-muted-foreground">{fir.title}</p>
        </div>
        <div className="flex gap-2 flex-wrap">
          <Link href={`/network?fir=${fir.id}`}><Button variant="outline" size="sm"><Network className="h-4 w-4" /> Graph</Button></Link>
          <Link href={`/heatmap?district=${fir.district}`}><Button variant="outline" size="sm"><Map className="h-4 w-4" /> Map</Button></Link>
          <a href={pdfUrl} target="_blank"><Button size="sm"><Download className="h-4 w-4" /> PDF Report</Button></a>
        </div>
      </div>

      <div className="flex gap-2 flex-wrap">
        <Badge>{fir.crime_type.replace(/_/g, " ")}</Badge>
        <Badge variant="outline">{fir.status.replace(/_/g, " ")}</Badge>
        <Badge variant={fir.priority === "critical" ? "destructive" : "warning"}>{fir.priority}</Badge>
        {fir.is_solved && <Badge variant="success">Solved</Badge>}
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle>Case Details</CardTitle></CardHeader>
          <CardContent className="space-y-4">
            <p className="text-sm leading-relaxed">{fir.description}</p>
            {fir.summary && <p className="text-sm text-muted-foreground border-l-2 border-primary pl-4">{fir.summary}</p>}
            <div className="grid grid-cols-2 gap-4 text-sm">
              <div><span className="text-muted-foreground">Incident:</span> {formatDate(fir.incident_date)}</div>
              <div><span className="text-muted-foreground">Registered:</span> {formatDate(fir.registered_date)}</div>
              <div><span className="text-muted-foreground">District:</span> {fir.district}</div>
              <div><span className="text-muted-foreground">Station:</span> {fir.station_name}</div>
            </div>
            {fir.ipc_sections && (
              <div className="flex gap-2 flex-wrap">
                {fir.ipc_sections.map((s) => <Badge key={s} variant="secondary">{s}</Badge>)}
              </div>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Timeline</CardTitle></CardHeader>
          <CardContent>
            <div className="space-y-4">
              {fir.timeline.map((t, i) => (
                <div key={i} className="flex gap-3">
                  <div className="w-2 h-2 rounded-full bg-primary mt-2 shrink-0" />
                  <div>
                    <p className="text-sm">{t.event}</p>
                    <p className="text-xs text-muted-foreground">{formatDate(t.date)}</p>
                  </div>
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card>
          <CardHeader><CardTitle>Accused ({fir.criminals.length})</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {fir.criminals.map((c) => (
              <Link key={c.id} href={`/criminals/${c.id}`} className="block p-2 rounded-lg hover:bg-secondary">
                <p className="text-sm font-medium">{c.name}</p>
                <p className="text-xs text-muted-foreground">Risk: {c.risk_score} • {c.role}</p>
              </Link>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Victims ({fir.victims.length})</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {fir.victims.map((v) => (
              <div key={v.id} className="p-2 rounded-lg bg-secondary/50">
                <p className="text-sm font-medium">{v.name}</p>
                {v.age && <p className="text-xs text-muted-foreground">Age: {v.age}</p>}
              </div>
            ))}
          </CardContent>
        </Card>
        <Card>
          <CardHeader><CardTitle>Evidence ({fir.evidence.length})</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {fir.evidence.map((e) => (
              <div key={e.id} className="p-2 rounded-lg bg-secondary/50">
                <div className="flex items-center gap-2">
                  <Badge variant="outline" className="text-xs">{e.evidence_type}</Badge>
                  {e.is_verified && <Badge variant="success" className="text-xs">Verified</Badge>}
                </div>
                <p className="text-xs mt-1">{e.description}</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function FIRDetailPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><FIRDetailContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
