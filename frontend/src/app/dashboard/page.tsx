"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import Link from "next/link";
import { motion } from "framer-motion";
import {
  FileText, CheckCircle, AlertTriangle, Users, TrendingUp, Bell, ArrowUpRight,
} from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, DashboardStats, Alert } from "@/lib/api";
import { formatNumber, formatDate } from "@/lib/utils";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function StatCard({ title, value, icon: Icon, trend, color }: {
  title: string; value: number; icon: React.ElementType; trend?: string; color: string;
}) {
  return (
    <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }}>
      <Card className="hover:border-primary/30 transition-colors">
        <CardContent className="p-6">
          <div className="flex items-start justify-between">
            <div>
              <p className="text-sm text-muted-foreground">{title}</p>
              <p className="text-3xl font-bold mt-1">{formatNumber(value)}</p>
              {trend && <p className="text-xs text-primary mt-1">{trend}</p>}
            </div>
            <div className={`p-3 rounded-lg ${color}`}>
              <Icon className="h-5 w-5" />
            </div>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}

function DashboardContent() {
  const [stats, setStats] = useState<DashboardStats | null>(null);
  const [trends, setTrends] = useState<{ date: string; count: number }[]>([]);
  const [crimeTypes, setCrimeTypes] = useState<{ crime_type: string; count: number }[]>([]);
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [hotspots, setHotspots] = useState<{ district: string; count: number }[]>([]);

  useEffect(() => {
    Promise.all([
      api.get<DashboardStats>("/analytics/dashboard"),
      api.get<{ date: string; count: number }[]>("/analytics/trends?days=30"),
      api.get<{ crime_type: string; count: number }[]>("/analytics/crime-types"),
      api.get<{ items: Alert[] }>("/alerts?unread_only=true&page_size=5"),
      api.get<{ district: string; total: number; solved: number; solve_rate: number }[]>("/analytics/district-comparison"),
    ]).then(([s, t, ct, a, h]) => {
      setStats(s);
      setTrends(t);
      setCrimeTypes(ct.slice(0, 8));
      setAlerts(a.items);
      setHotspots(h.slice(0, 5).map((d) => ({ district: d.district, count: d.total })));
    }).catch(console.error);
  }, []);

  const trendOption = {
    backgroundColor: "transparent",
    tooltip: { trigger: "axis" },
    grid: { left: 40, right: 20, top: 20, bottom: 30 },
    xAxis: { type: "category", data: trends.map((t) => t.date.slice(5)), axisLabel: { color: "#94a3b8" } },
    yAxis: { type: "value", axisLabel: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "#1e3a5f" } } },
    series: [{
      data: trends.map((t) => t.count),
      type: "line",
      smooth: true,
      areaStyle: { color: { type: "linear", x: 0, y: 0, x2: 0, y2: 1, colorStops: [
        { offset: 0, color: "rgba(8,145,178,0.4)" }, { offset: 1, color: "rgba(8,145,178,0)" }
      ]}},
      lineStyle: { color: "#0891b2" },
      itemStyle: { color: "#0891b2" },
    }],
  };

  const pieOption = {
    backgroundColor: "transparent",
    tooltip: { trigger: "item" },
    series: [{
      type: "pie",
      radius: ["45%", "70%"],
      data: crimeTypes.map((c) => ({ name: c.crime_type.replace(/_/g, " "), value: c.count })),
      label: { color: "#94a3b8", fontSize: 10 },
      itemStyle: { borderRadius: 4, borderColor: "#0b1120", borderWidth: 2 },
    }],
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Intelligence Dashboard</h1>
        <p className="text-muted-foreground">Real-time crime analytics and alerts overview</p>
      </div>

      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Total FIRs" value={stats?.total_firs ?? 0} icon={FileText} color="bg-blue-500/20 text-blue-400" />
        <StatCard title="Solved Cases" value={stats?.solved_cases ?? 0} icon={CheckCircle} color="bg-green-500/20 text-green-400" />
        <StatCard title="Active Investigations" value={stats?.active_investigations ?? 0} icon={AlertTriangle} color="bg-yellow-500/20 text-yellow-400" />
        <StatCard title="Repeat Offenders" value={stats?.repeat_offenders ?? 0} icon={Users} color="bg-red-500/20 text-red-400" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader><CardTitle className="flex items-center gap-2"><TrendingUp className="h-5 w-5 text-primary" /> Crime Trends (30 Days)</CardTitle></CardHeader>
          <CardContent>{trends.length > 0 && <ReactECharts option={trendOption} style={{ height: 300 }} />}</CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Crime Type Distribution</CardTitle></CardHeader>
          <CardContent>{crimeTypes.length > 0 && <ReactECharts option={pieOption} style={{ height: 300 }} />}</CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="flex items-center gap-2"><Bell className="h-5 w-5 text-primary" /> Live Alerts</CardTitle>
            <Link href="/alerts" className="text-sm text-primary flex items-center gap-1">View all <ArrowUpRight className="h-3 w-3" /></Link>
          </CardHeader>
          <CardContent className="space-y-3">
            {alerts.length === 0 ? (
              <p className="text-muted-foreground text-sm">No unread alerts</p>
            ) : alerts.map((a) => (
              <div key={a.id} className="flex items-start gap-3 p-3 rounded-lg bg-secondary/50">
                <Badge variant={a.severity === "critical" ? "destructive" : a.severity === "warning" ? "warning" : "default"}>
                  {a.severity}
                </Badge>
                <div className="flex-1 min-w-0">
                  <p className="text-sm font-medium truncate">{a.title}</p>
                  <p className="text-xs text-muted-foreground">{formatDate(a.created_at)}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Hotspot Summary</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {hotspots.map((h, i) => (
              <div key={h.district} className="flex items-center justify-between">
                <div className="flex items-center gap-3">
                  <span className="text-xs text-muted-foreground w-4">{i + 1}</span>
                  <span className="text-sm">{h.district}</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="h-2 rounded-full bg-primary" style={{ width: `${Math.min(100, h.count / 10)}px` }} />
                  <span className="text-sm font-mono text-primary">{formatNumber(h.count)}</span>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function DashboardPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><DashboardContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
