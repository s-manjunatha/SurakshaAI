"use client";

import { useState } from "react";
import Link from "next/link";
import { Search } from "lucide-react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { api } from "@/lib/api";

interface SimilarCase {
  fir_id: string;
  fir_number: string;
  title: string;
  crime_type: string;
  similarity_score: number;
  summary?: string;
}

function SimilarCasesContent() {
  const [query, setQuery] = useState("");
  const [results, setResults] = useState<SimilarCase[]>([]);
  const [loading, setLoading] = useState(false);

  const search = async () => {
    if (!query.trim()) return;
    setLoading(true);
    try {
      const res = await api.post<SimilarCase[]>("/ai/similar-cases", { query, n: 10 });
      setResults(res);
    } catch {
      setResults([]);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Similar Case Retrieval</h1>
        <p className="text-muted-foreground">Semantic search powered by ChromaDB vector embeddings</p>
      </div>

      <Card>
        <CardContent className="p-4 flex gap-3">
          <div className="relative flex-1">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 h-4 w-4 text-muted-foreground" />
            <Input className="pl-10" placeholder="Describe a case to find similar FIRs..." value={query} onChange={(e) => setQuery(e.target.value)} onKeyDown={(e) => e.key === "Enter" && search()} />
          </div>
          <Button onClick={search} disabled={loading}>{loading ? "Searching..." : "Search"}</Button>
        </CardContent>
      </Card>

      <div className="space-y-3">
        {results.map((r) => (
          <Link key={r.fir_id} href={`/fir/${r.fir_id}`}>
            <Card className="hover:border-primary/40 transition-colors cursor-pointer">
              <CardContent className="p-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 mb-1">
                      <span className="font-mono text-sm text-primary">{r.fir_number}</span>
                      <Badge variant="outline">{r.crime_type.replace(/_/g, " ")}</Badge>
                    </div>
                    <p className="font-medium">{r.title}</p>
                    {r.summary && <p className="text-sm text-muted-foreground mt-1 line-clamp-2">{r.summary}</p>}
                  </div>
                  <div className="text-center shrink-0">
                    <p className="text-2xl font-bold text-primary">{(r.similarity_score * 100).toFixed(0)}%</p>
                    <p className="text-xs text-muted-foreground">match</p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </Link>
        ))}
        {results.length === 0 && !loading && (
          <p className="text-center text-muted-foreground py-12">Enter a case description to find similar FIRs</p>
        )}
      </div>
    </div>
  );
}

export default function SimilarCasesPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><SimilarCasesContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
