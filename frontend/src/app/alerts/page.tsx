"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { api, Alert, Paginated } from "@/lib/api";
import { formatDate } from "@/lib/utils";

function AlertsContent() {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [filter, setFilter] = useState<"all" | "unread">("unread");

  const load = () => {
    const params = filter === "unread" ? "?unread_only=true&page_size=50" : "?page_size=50";
    api.get<Paginated<Alert>>(`/alerts${params}`).then((r) => setAlerts(r.items)).catch(console.error);
  };

  useEffect(() => { load(); }, [filter]);

  const markRead = async (id: string) => {
    await api.patch(`/alerts/${id}/read`);
    load();
  };

  const generate = async () => {
    await api.post("/alerts/generate");
    load();
  };

  return (
    <div className="space-y-6">
      <div className="flex items-center justify-between flex-wrap gap-4">
        <div>
          <h1 className="text-2xl font-bold">Alert System</h1>
          <p className="text-muted-foreground">Repeat offenders, gang activity, and crime spike detection</p>
        </div>
        <div className="flex gap-2">
          <Button variant={filter === "unread" ? "default" : "outline"} size="sm" onClick={() => setFilter("unread")}>Unread</Button>
          <Button variant={filter === "all" ? "default" : "outline"} size="sm" onClick={() => setFilter("all")}>All</Button>
          <Button variant="outline" size="sm" onClick={generate}>Generate Alerts</Button>
        </div>
      </div>

      <div className="space-y-3">
        {alerts.map((a) => (
          <Card key={a.id} className={!a.is_read ? "border-primary/30" : ""}>
            <CardContent className="p-4 flex items-start gap-4">
              <Badge variant={a.severity === "critical" ? "destructive" : a.severity === "warning" ? "warning" : "default"}>
                {a.severity}
              </Badge>
              <div className="flex-1">
                <div className="flex items-center gap-2 mb-1">
                  <Badge variant="outline" className="text-xs">{a.alert_type.replace(/_/g, " ")}</Badge>
                  {!a.is_read && <Badge variant="secondary" className="text-xs">New</Badge>}
                </div>
                <p className="font-medium">{a.title}</p>
                <p className="text-sm text-muted-foreground mt-1">{a.message}</p>
                <p className="text-xs text-muted-foreground mt-2">{formatDate(a.created_at)} {a.district && `• ${a.district}`}</p>
              </div>
              {!a.is_read && (
                <Button variant="outline" size="sm" onClick={() => markRead(a.id)}>Mark Read</Button>
              )}
            </CardContent>
          </Card>
        ))}
        {alerts.length === 0 && (
          <p className="text-center text-muted-foreground py-12">No alerts. Click Generate Alerts to scan for patterns.</p>
        )}
      </div>
    </div>
  );
}

export default function AlertsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><AlertsContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
