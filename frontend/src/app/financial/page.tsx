"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/sidebar";
import { ProtectedRoute } from "@/components/layout/protected-route";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { api, Paginated } from "@/lib/api";
import { formatDate } from "@/lib/utils";

interface Transaction {
  id: string;
  amount: number;
  transaction_date: string;
  transaction_type?: string;
  is_suspicious: boolean;
  suspicion_reason?: string;
  from_account?: string;
  to_account?: string;
}

function FinancialContent() {
  const [transactions, setTransactions] = useState<Transaction[]>([]);
  const [patterns, setPatterns] = useState<{ account: string; bank: string; transactions: number; total_amount: number; suspicious: number }[]>([]);
  const [flagged, setFlagged] = useState<{ id: string; account_number: string; bank_name: string; holder?: string }[]>([]);
  const [suspiciousOnly, setSuspiciousOnly] = useState(true);

  useEffect(() => {
    api.get<Paginated<Transaction>>(`/financial/transactions?suspicious_only=${suspiciousOnly}&page_size=20`).then((r) => setTransactions(r.items)).catch(console.error);
    api.get<typeof patterns>("/financial/suspicious-patterns").then(setPatterns).catch(console.error);
    api.get<typeof flagged>("/financial/flagged-accounts").then(setFlagged).catch(console.error);
  }, [suspiciousOnly]);

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold">Financial Crime Module</h1>
        <p className="text-muted-foreground">Bank transaction tracking and money trail analysis</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <Card className="lg:col-span-2">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle>Transactions</CardTitle>
            <label className="flex items-center gap-2 text-sm">
              <input type="checkbox" checked={suspiciousOnly} onChange={(e) => setSuspiciousOnly(e.target.checked)} />
              Suspicious only
            </label>
          </CardHeader>
          <CardContent>
            <div className="overflow-x-auto">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b border-border text-muted-foreground">
                    <th className="text-left py-2">Date</th>
                    <th className="text-left py-2">From</th>
                    <th className="text-left py-2">To</th>
                    <th className="text-right py-2">Amount</th>
                    <th className="text-left py-2">Type</th>
                    <th className="text-left py-2">Status</th>
                  </tr>
                </thead>
                <tbody>
                  {transactions.map((t) => (
                    <tr key={t.id} className="border-b border-border/50">
                      <td className="py-2">{formatDate(t.transaction_date)}</td>
                      <td className="py-2 font-mono text-xs">{t.from_account?.slice(-6)}</td>
                      <td className="py-2 font-mono text-xs">{t.to_account?.slice(-6)}</td>
                      <td className="py-2 text-right font-mono">₹{t.amount.toLocaleString("en-IN")}</td>
                      <td className="py-2">{t.transaction_type}</td>
                      <td className="py-2">{t.is_suspicious ? <Badge variant="destructive">Suspicious</Badge> : <Badge variant="outline">Normal</Badge>}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </CardContent>
        </Card>

        <div className="space-y-6">
          <Card>
            <CardHeader><CardTitle>Flagged Accounts</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {flagged.slice(0, 8).map((a) => (
                <div key={a.id} className="p-2 rounded bg-secondary/50 text-sm">
                  <p className="font-mono">{a.account_number}</p>
                  <p className="text-xs text-muted-foreground">{a.bank_name} • {a.holder}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card>
            <CardHeader><CardTitle>Suspicious Patterns</CardTitle></CardHeader>
            <CardContent className="space-y-2">
              {patterns.slice(0, 6).map((p, i) => (
                <div key={i} className="p-2 rounded bg-secondary/50 text-sm">
                  <p className="font-mono">{p.account}</p>
                  <p className="text-xs text-muted-foreground">{p.bank} • {p.transactions} txns • ₹{p.total_amount.toLocaleString("en-IN")}</p>
                  {p.suspicious > 0 && <Badge variant="destructive" className="mt-1">{p.suspicious} suspicious</Badge>}
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </div>
    </div>
  );
}

export default function FinancialPage() {
  return (
    <ProtectedRoute>
      <DashboardLayout><FinancialContent /></DashboardLayout>
    </ProtectedRoute>
  );
}
