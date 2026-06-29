"use client";

import { useEffect, useState } from "react";
import { useParams } from "next/navigation";
import Link from "next/link";
import { ArrowLeft } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface CriminalDetail extends Record<string, unknown> {
  id: string;
  name: string;
  alias?: string;
  age?: number;
  gender?: string;
  address?: string;
  district?: string;
  risk_score: number;
  is_repeat_offender: boolean;
  gang_affiliation?: string;
  modus_operandi?: string;
  fir_count: number;
  vehicles: { registration: string; make: string; model: string }[];
  phones: { number: string; operator: string }[];
  bank_accounts: { account: string; bank: string; flagged: boolean }[];
  associated_persons: { id: string; name: string; risk_score: number }[];
  crime_history: { fir_number: string; crime_type: string; date: string; status: string }[];
}

function CriminalDetailContent() {
  const params = useParams();
  const [criminal, setCriminal] = useState<CriminalDetail | null>(null);

  useEffect(() => {
    if (params.id) api.get<CriminalDetail>(`/criminals/${params.id}`).then(setCriminal).catch(console.error);
  }, [params.id]);

  if (!criminal) return <div className="text-center py-12 text-muted-foreground">Loading profile...</div>;

  return (
    <div className="space-y-6">
      <Link href="/criminals" className="text-sm text-muted-foreground flex items-center gap-1 hover:text-primary">
        <ArrowLeft className="h-4 w-4" /> Back to Profiles
      </Link>

      <div className="flex items-start gap-6 flex-wrap">
        <div className="h-20 w-20 rounded-2xl bg-navy flex items-center justify-center text-3xl font-bold text-primary">
          {criminal.name.charAt(0)}
        </div>
        <div className="flex-1">
          <h1 className="text-2xl font-bold">{criminal.name}</h1>
          {criminal.alias && <p className="text-muted-foreground">Alias: {criminal.alias}</p>}
          <div className="flex gap-2 mt-2 flex-wrap">
            {criminal.is_repeat_offender && <Badge variant="destructive">Repeat Offender</Badge>}
            {criminal.gang_affiliation && <Badge variant="warning">{criminal.gang_affiliation}</Badge>}
            <Badge variant="outline">{criminal.fir_count} FIRs</Badge>
          </div>
        </div>
        <Card className="w-48">
          <CardContent className="p-4 text-center">
            <p className="text-xs text-muted-foreground">Risk Score</p>
            <p className={`text-4xl font-bold ${criminal.risk_score > 70 ? "text-red-400" : "text-primary"}`}>{criminal.risk_score}</p>
            <p className="text-xs text-muted-foreground">out of 100</p>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Personal Details</CardTitle></CardHeader>
          <CardContent className="grid grid-cols-2 gap-3 text-sm">
            <div><span className="text-muted-foreground">Age:</span> {criminal.age}</div>
            <div><span className="text-muted-foreground">Gender:</span> {criminal.gender}</div>
            <div className="col-span-2"><span className="text-muted-foreground">Address:</span> {criminal.address}</div>
            <div><span className="text-muted-foreground">District:</span> {criminal.district}</div>
            {criminal.modus_operandi && <div className="col-span-2"><span className="text-muted-foreground">MO:</span> {criminal.modus_operandi}</div>}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Crime History</CardTitle></CardHeader>
          <CardContent className="space-y-2 max-h-64 overflow-y-auto">
            {criminal.crime_history.map((c, i) => (
              <div key={i} className="flex justify-between p-2 rounded bg-secondary/50 text-sm">
                <span className="font-mono text-primary">{c.fir_number}</span>
                <span>{c.crime_type.replace(/_/g, " ")}</span>
                <span className="text-muted-foreground">{formatDate(c.date)}</span>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Linked Assets</CardTitle></CardHeader>
          <CardContent className="space-y-3 text-sm">
            <div><p className="text-muted-foreground mb-1">Vehicles</p>{criminal.vehicles.map((v, i) => <p key={i}>{v.registration} — {v.make} {v.model}</p>)}</div>
            <div><p className="text-muted-foreground mb-1">Phones</p>{criminal.phones.map((p, i) => <p key={i}>{p.number} ({p.operator})</p>)}</div>
            <div><p className="text-muted-foreground mb-1">Bank Accounts</p>{criminal.bank_accounts.map((b, i) => <p key={i}>{b.account} — {b.bank} {b.flagged && "⚠"}</p>)}</div>
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Associated Persons</CardTitle></CardHeader>
          <CardContent className="space-y-2">
            {criminal.associated_persons.map((p) => (
              <Link key={p.id} href={`/criminals/${p.id}`} className="flex justify-between p-2 rounded hover:bg-secondary text-sm">
                <span>{p.name}</span>
                <span className="text-muted-foreground">Risk: {p.risk_score}</span>
              </Link>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function CriminalDetailPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><CriminalDetailContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
