"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function AnalyticsContent() {
  const [crimeTypes, setCrimeTypes] = useState<{ crime_type: string; count: number }[]>([]);
  const [demographics, setDemographics] = useState<{ age_group: string; gender: string; count: number }[]>([]);
  const [districts, setDistricts] = useState<{ district: string; total: number; solved: number; solve_rate: number }[]>([]);
  const [seasonal, setSeasonal] = useState<{ month: string; crime_type: string; count: number }[]>([]);
  const [trends, setTrends] = useState<{ date: string; count: number }[]>([]);

  useEffect(() => {
    Promise.all([
      api.get<typeof crimeTypes>("/analytics/crime-types"),
      api.get<typeof demographics>("/analytics/demographics"),
      api.get<typeof districts>("/analytics/district-comparison"),
      api.get<typeof seasonal>("/analytics/seasonal"),
      api.get<typeof trends>("/analytics/trends?days=180"),
    ]).then(([ct, d, dist, s, t]) => {
      setCrimeTypes(ct); setDemographics(d); setDistricts(dist); setSeasonal(s); setTrends(t);
    }).catch(console.error);
  }, []);

  const chartBase = { backgroundColor: "transparent", textStyle: { color: "#94a3b8" } };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Crime Analytics</h1>
        <p className="text-muted-foreground">Time-series, demographics, and geographic analysis</p>
      </div>

      <Card>
        <CardHeader><CardTitle>180-Day Crime Trend</CardTitle></CardHeader>
        <CardContent>
          <ReactECharts option={{
            ...chartBase, tooltip: { trigger: "axis" },
            xAxis: { type: "category", data: trends.map((t) => t.date.slice(5)) },
            yAxis: { type: "value", splitLine: { lineStyle: { color: "#1e3a5f" } } },
            series: [{ type: "bar", data: trends.map((t) => t.count), itemStyle: { color: "#0891b2" } }],
          }} style={{ height: 300 }} />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Crime Type Distribution</CardTitle></CardHeader>
          <CardContent>
            <ReactECharts option={{
              ...chartBase, tooltip: { trigger: "item" },
              series: [{ type: "pie", radius: "65%", data: crimeTypes.slice(0, 10).map((c) => ({ name: c.crime_type.replace(/_/g, " "), value: c.count })) }],
            }} style={{ height: 350 }} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Age/Gender Distribution</CardTitle></CardHeader>
          <CardContent>
            <ReactECharts option={{
              ...chartBase, tooltip: { trigger: "axis" }, legend: { data: ["Male", "Female"], textStyle: { color: "#94a3b8" } },
              xAxis: { type: "category", data: [...new Set(demographics.map((d) => d.age_group))] },
              yAxis: { type: "value" },
              series: ["Male", "Female"].map((g) => ({
                name: g, type: "bar", stack: "total",
                data: [...new Set(demographics.map((d) => d.age_group))].map(
                  (ag) => demographics.find((d) => d.age_group === ag && d.gender === g)?.count || 0
                ),
              })),
            }} style={{ height: 350 }} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>District Comparison</CardTitle></CardHeader>
          <CardContent>
            <ReactECharts option={{
              ...chartBase, tooltip: { trigger: "axis" },
              xAxis: { type: "category", data: districts.slice(0, 10).map((d) => d.district.split(" ")[0]), axisLabel: { rotate: 30 } },
              yAxis: { type: "value" },
              series: [
                { name: "Total", type: "bar", data: districts.slice(0, 10).map((d) => d.total), itemStyle: { color: "#0891b2" } },
                { name: "Solved", type: "bar", data: districts.slice(0, 10).map((d) => d.solved), itemStyle: { color: "#22c55e" } },
              ],
            }} style={{ height: 350 }} />
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Seasonal Trends</CardTitle></CardHeader>
          <CardContent>
            <ReactECharts option={{
              ...chartBase, tooltip: { trigger: "axis" },
              xAxis: { type: "category", data: [...new Set(seasonal.map((s) => s.month))] },
              yAxis: { type: "value" },
              series: [...new Set(seasonal.map((s) => s.crime_type))].slice(0, 5).map((ct) => ({
                name: ct.replace(/_/g, " "), type: "line", smooth: true,
                data: [...new Set(seasonal.map((s) => s.month))].map(
                  (m) => seasonal.find((s) => s.month === m && s.crime_type === ct)?.count || 0
                ),
              })),
            }} style={{ height: 350 }} />
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function AnalyticsPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><AnalyticsContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
