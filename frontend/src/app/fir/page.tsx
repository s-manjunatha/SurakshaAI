"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, Filter, ChevronRight } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, FIR, Paginated } from "@/lib/api";
import { formatDate } from "@/lib/utils";

const priorityVariant = (p: string) => p === "critical" ? "destructive" : p === "high" ? "warning" : "default";

function FIRListContent() {
  const [firs, setFirs] = useState<FIR[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [crimeType, setCrimeType] = useState("");
  const [status, setStatus] = useState("");
  const [loading, setLoading] = useState(true);

  const loadFirs = () => {
    setLoading(true);
    const params = new URLSearchParams({ page: String(page), page_size: "20" });
    if (search) params.set("search", search);
    if (crimeType) params.set("crime_type", crimeType);
    if (status) params.set("status", status);
    api.get<Paginated<FIR>>(`/fir?${params}`)
      .then((res) => { setFirs(res.items); setTotal(res.total); })
      .catch(console.error)
      .finally(() => setLoading(false));
  };

  useEffect(() => { loadFirs(); }, [page, crimeType, status]);

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">FIR Management</h1>
          <p className="text-muted-foreground">{total.toLocaleString()} records</p>
        </div>
      </div>

      <Card>
        <CardContent className="p-4">
          <div className="flex flex-col sm:flex-row gap-3">
            <div className="relative flex-1">
              <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
              <Input className="pl-10" placeholder="Search FIR number, title..." value={search} onChange={(e) => setSearch(e.target.value)} onKeyDown={(e) => e.key === "Enter" && loadFirs()} />
            </div>
            <select className="h-10 rounded-lg border border-border bg-input px-3 text-sm" value={crimeType} onChange={(e) => { setCrimeType(e.target.value); setPage(1); }}>
              <option value="">All Crime Types</option>
              {["theft", "robbery", "murder", "fraud", "cyber_crime", "chain_snatching", "assault"].map((t) => (
                <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
              ))}
            </select>
            <select className="h-10 rounded-lg border border-border bg-input px-3 text-sm" value={status} onChange={(e) => { setStatus(e.target.value); setPage(1); }}>
              <option value="">All Status</option>
              {["registered", "under_investigation", "closed", "convicted"].map((s) => (
                <option key={s} value={s}>{s.replace(/_/g, " ")}</option>
              ))}
            </select>
            <Button onClick={loadFirs}><Filter className="h-4 w-4" /> Filter</Button>
          </div>
        </CardContent>
      </Card>

      <div className="space-y-2">
        {loading ? (
          <div className="text-center py-12 text-muted-foreground">Loading FIRs...</div>
        ) : firs.length === 0 ? (
          <div className="text-center py-12 text-muted-foreground">No FIRs found. Run data generation script.</div>
        ) : firs.map((fir) => (
          <Link key={fir.id} href={`/fir/${fir.id}`}>
            <Card className="hover:border-primary/40 transition-colors cursor-pointer">
              <CardContent className="p-4 flex items-center gap-4">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 flex-wrap mb-1">
                    <span className="font-mono text-sm text-primary">{fir.fir_number}</span>
                    <Badge variant={priorityVariant(fir.priority)}>{fir.priority}</Badge>
                    <Badge variant="outline">{fir.crime_type.replace(/_/g, " ")}</Badge>
                    {fir.is_solved && <Badge variant="success">Solved</Badge>}
                  </div>
                  <p className="font-medium truncate">{fir.title}</p>
                  <p className="text-xs text-muted-foreground mt-1">
                    {fir.district || "Unknown"} • {formatDate(fir.incident_date)} • {fir.status.replace(/_/g, " ")}
                  </p>
                </div>
                <ChevronRight className="h-5 w-5 text-muted-foreground shrink-0" />
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="flex justify-center gap-2">
        <Button variant="outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
        <span className="flex items-center px-4 text-sm text-muted-foreground">Page {page}</span>
        <Button variant="outline" disabled={firs.length < 20} onClick={() => setPage(page + 1)}>Next</Button>
      </div>
    </div>
  );
}

export default function FIRPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><FIRListContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
