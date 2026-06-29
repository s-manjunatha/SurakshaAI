"use client";

import { useEffect, useState } from "react";
import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

const ReactECharts = dynamic(() => import("echarts-for-react"), { ssr: false });

function ForecastContent() {
  const [volume, setVolume] = useState<{ date: string; predicted_count: number; lower_bound: number; upper_bound: number }[]>([]);
  const [hotspots, setHotspots] = useState<{ latitude: number; longitude: number; district: string; predicted_intensity: number; risk_level: string }[]>([]);
  const [regions, setRegions] = useState<{ district: string; risk_score: number; crime_count: number; trend: string }[]>([]);

  useEffect(() => {
    Promise.all([
      api.get<typeof volume>("/forecast/volume?periods=30"),
      api.get<typeof hotspots>("/forecast/hotspots"),
      api.get<typeof regions>("/forecast/region-risk"),
    ]).then(([v, h, r]) => { setVolume(v); setHotspots(h); setRegions(r); }).catch(console.error);
  }, []);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Crime Forecasting</h1>
        <p className="text-muted-foreground">ML-powered predictions using Prophet & sklearn</p>
      </div>

      <Card>
        <CardHeader><CardTitle>30-Day Crime Volume Forecast</CardTitle></CardHeader>
        <CardContent>
          <ReactECharts option={{
            backgroundColor: "transparent",
            tooltip: { trigger: "axis" },
            xAxis: { type: "category", data: volume.map((v) => v.date.slice(5)), axisLabel: { color: "#94a3b8" } },
            yAxis: { type: "value", axisLabel: { color: "#94a3b8" }, splitLine: { lineStyle: { color: "#1e3a5f" } } },
            series: [
              { name: "Predicted", type: "line", data: volume.map((v) => v.predicted_count), lineStyle: { color: "#0891b2" }, itemStyle: { color: "#0891b2" } },
              { name: "Upper", type: "line", data: volume.map((v) => v.upper_bound), lineStyle: { type: "dashed", color: "#475569" }, showSymbol: false },
              { name: "Lower", type: "line", data: volume.map((v) => v.lower_bound), lineStyle: { type: "dashed", color: "#475569" }, showSymbol: false },
            ],
          }} style={{ height: 350 }} />
        </CardContent>
      </Card>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <Card>
          <CardHeader><CardTitle>Predicted Hotspots</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {hotspots.map((h, i) => (
              <div key={i} className="flex items-center justify-between p-3 rounded-lg bg-secondary/50">
                <div>
                  <p className="text-sm font-medium">{h.district}</p>
                  <p className="text-xs text-muted-foreground">{h.latitude.toFixed(4)}, {h.longitude.toFixed(4)}</p>
                </div>
                <div className="text-right">
                  <Badge variant={h.risk_level === "high" ? "destructive" : "warning"}>{h.risk_level}</Badge>
                  <p className="text-sm font-mono text-primary mt-1">{h.predicted_intensity}</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card>
          <CardHeader><CardTitle>Regional Risk Scores</CardTitle></CardHeader>
          <CardContent className="space-y-3">
            {regions.slice(0, 10).map((r, i) => (
              <div key={i} className="flex items-center gap-3">
                <span className="text-xs text-muted-foreground w-4">{i + 1}</span>
                <div className="flex-1">
                  <div className="flex justify-between text-sm mb-1">
                    <span>{r.district}</span>
                    <span className="font-mono text-primary">{r.risk_score}</span>
                  </div>
                  <div className="h-1.5 rounded-full bg-secondary overflow-hidden">
                    <div className="h-full bg-primary rounded-full" style={{ width: `${Math.min(100, r.risk_score)}%` }} />
                  </div>
                </div>
                <Badge variant={r.trend === "increasing" ? "destructive" : r.trend === "decreasing" ? "success" : "outline"} className="text-xs">
                  {r.trend}
                </Badge>
              </div>
            ))}
          </CardContent>
        </Card>
      </div>
    </div>
  );
}

export default function ForecastPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><ForecastContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
