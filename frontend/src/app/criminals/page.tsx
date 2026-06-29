"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Search, AlertTriangle } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, Criminal, Paginated } from "@/lib/api";

function CriminalsContent() {
  const [criminals, setCriminals] = useState<Criminal[]>([]);
  const [search, setSearch] = useState("");
  const [repeatOnly, setRepeatOnly] = useState(false);
  const [page, setPage] = useState(1);

  useEffect(() => {
    const params = new URLSearchParams({ page: String(page), page_size: "20" });
    if (search) params.set("search", search);
    if (repeatOnly) params.set("repeat_only", "true");
    api.get<Paginated<Criminal>>(`/criminals?${params}`).then((r) => setCriminals(r.items)).catch(console.error);
  }, [search, repeatOnly, page]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Criminal Profiles</h1>
        <p className="text-muted-foreground">Offender profiling and risk scoring</p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <div className="relative flex-1 min-w-[200px]">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
          <Input className="pl-10" placeholder="Search by name..." value={search} onChange={(e) => setSearch(e.target.value)} />
        </div>
        <Button variant={repeatOnly ? "default" : "outline"} onClick={() => setRepeatOnly(!repeatOnly)}>
          <AlertTriangle className="h-4 w-4" /> Repeat Offenders
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {criminals.map((c) => (
          <Link key={c.id} href={`/criminals/${c.id}`}>
            <Card className="hover:border-primary/40 transition-colors cursor-pointer h-full">
              <CardContent className="p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="font-semibold">{c.name}</h3>
                    {c.alias && <p className="text-xs text-muted-foreground">Alias: {c.alias}</p>}
                  </div>
                  {c.is_repeat_offender && <Badge variant="destructive">Repeat</Badge>}
                </div>
                <div className="space-y-2">
                  <div className="flex justify-between text-sm">
                    <span className="text-muted-foreground">Risk Score</span>
                    <span className={`font-bold ${c.risk_score > 70 ? "text-red-400" : c.risk_score > 40 ? "text-yellow-400" : "text-green-400"}`}>
                      {c.risk_score}/100
                    </span>
                  </div>
                  <div className="h-2 rounded-full bg-secondary overflow-hidden">
                    <div className="h-full rounded-full bg-primary transition-all" style={{ width: `${c.risk_score}%` }} />
                  </div>
                  <p className="text-xs text-muted-foreground">{c.district} • {c.gender} • {c.age} yrs</p>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
      </div>

      <div className="flex justify-center gap-2">
        <Button variant="outline" disabled={page <= 1} onClick={() => setPage(page - 1)}>Previous</Button>
        <Button variant="outline" onClick={() => setPage(page + 1)}>Next</Button>
      </div>
    </div>
  );
}

export default function CriminalsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><CriminalsContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
