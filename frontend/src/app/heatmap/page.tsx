"use client";

import { useEffect, useState } from "react";
import { useSearchParams } from "next/navigation";
import dynamic from "next/dynamic";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { api } from "@/lib/api";

import "leaflet/dist/leaflet.css";

const MapContainer = dynamic(() => import("react-leaflet").then((m) => m.MapContainer), { ssr: false });
const TileLayer = dynamic(() => import("react-leaflet").then((m) => m.TileLayer), { ssr: false });
const CircleMarker = dynamic(() => import("react-leaflet").then((m) => m.CircleMarker), { ssr: false });
const Popup = dynamic(() => import("react-leaflet").then((m) => m.Popup), { ssr: false });

interface Hotspot {
  latitude: number;
  longitude: number;
  count: number;
  district: string;
  crime_type?: string;
}

function HeatmapContent() {
  const searchParams = useSearchParams();
  const [hotspots, setHotspots] = useState<Hotspot[]>([]);
  const [crimeType, setCrimeType] = useState("");
  const [district, setDistrict] = useState(searchParams.get("district") || "");
  const [days, setDays] = useState(90);

  useEffect(() => {
    const params = new URLSearchParams({ days: String(days) });
    if (crimeType) params.set("crime_type", crimeType);
    if (district) params.set("district", district);
    api.get<Hotspot[]>(`/analytics/hotspots?${params}`).then(setHotspots).catch(console.error);
  }, [crimeType, district, days]);

  const maxCount = Math.max(...hotspots.map((h) => h.count), 1);
  const center: [number, number] = hotspots.length > 0
    ? [hotspots.reduce((s, h) => s + h.latitude, 0) / hotspots.length, hotspots.reduce((s, h) => s + h.longitude, 0) / hotspots.length]
    : [12.9716, 77.5946];

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Crime Heatmap</h1>
        <p className="text-muted-foreground">Hotspot visualization with density clustering</p>
      </div>

      <div className="flex gap-3 flex-wrap">
        <select className="h-10 rounded-lg border border-border bg-input px-3 text-sm" value={crimeType} onChange={(e) => setCrimeType(e.target.value)}>
          <option value="">All Crime Types</option>
          {["theft", "robbery", "murder", "chain_snatching", "fraud"].map((t) => (
            <option key={t} value={t}>{t.replace(/_/g, " ")}</option>
          ))}
        </select>
        <input className="h-10 rounded-lg border border-border bg-input px-3 text-sm" placeholder="District filter..." value={district} onChange={(e) => setDistrict(e.target.value)} />
        <select className="h-10 rounded-lg border border-border bg-input px-3 text-sm" value={days} onChange={(e) => setDays(Number(e.target.value))}>
          <option value={30}>Last 30 days</option>
          <option value={90}>Last 90 days</option>
          <option value={180}>Last 180 days</option>
          <option value={365}>Last year</option>
        </select>
      </div>

      <Card>
        <CardHeader><CardTitle>{hotspots.length} Hotspots Detected</CardTitle></CardHeader>
        <CardContent className="p-0 overflow-hidden rounded-b-xl">
          <MapContainer center={center} zoom={8} style={{ height: "550px", width: "100%" }}>
            <TileLayer url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png" attribution='&copy; OpenStreetMap' />
            {hotspots.map((h, i) => (
              <CircleMarker
                key={i}
                center={[h.latitude, h.longitude]}
                radius={Math.max(6, (h.count / maxCount) * 25)}
                pathOptions={{
                  color: h.count > maxCount * 0.7 ? "#ef4444" : h.count > maxCount * 0.4 ? "#f59e0b" : "#0891b2",
                  fillColor: h.count > maxCount * 0.7 ? "#ef4444" : h.count > maxCount * 0.4 ? "#f59e0b" : "#0891b2",
                  fillOpacity: 0.6,
                  weight: 1,
                }}
              >
                <Popup>
                  <strong>{h.district}</strong><br />
                  Crimes: {h.count}<br />
                  {h.crime_type && `Type: ${h.crime_type}`}
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </CardContent>
      </Card>
    </div>
  );
}

export default function HeatmapPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><HeatmapContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
