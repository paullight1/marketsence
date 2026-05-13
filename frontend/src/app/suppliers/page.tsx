"use client";

import { useEffect, useMemo, useState } from "react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { SupplierSummary, fetchJson } from "@/lib/api";

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 0,
  }).format(value);
}

function getTrustColor(score: number) {
  if (score >= 90) return "text-[#166534]";
  if (score >= 75) return "text-[#b45309]";
  return "text-[#c2413a]";
}

export default function SuppliersPage() {
  const [suppliers, setSuppliers] = useState<SupplierSummary[]>([]);
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("all");
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadSuppliers() {
      try {
        setSuppliers(await fetchJson<SupplierSummary[]>("/api/suppliers/?limit=100"));
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Could not load suppliers");
      }
    }

    loadSuppliers();
  }, []);

  const sources = useMemo(
    () => Array.from(new Set(suppliers.map((supplier) => supplier.source))).sort(),
    [suppliers],
  );

  const filteredSuppliers = suppliers.filter((supplier) => {
    const matchesSearch = supplier.name.toLowerCase().includes(search.toLowerCase());
    const matchesSource = source === "all" || supplier.source === source;
    return matchesSearch && matchesSource;
  });

  return (
    <WorkspaceShell>
      <section className="page-enter flex flex-col gap-2">
        <span className="metric-pill w-fit">Source quality</span>
        <h1 className="text-4xl font-semibold tracking-tight text-[#173b39]">
          Suppliers and source trust
        </h1>
        <p className="max-w-3xl text-sm text-[#48655d]">
          Review supplier reliability, suspicious counts, and pricing stability from the live backend.
        </p>
        {error ? (
          <p className="w-fit rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}
      </section>

      <section className="page-enter flex flex-wrap gap-4">
        <Input
          placeholder="Search suppliers..."
          value={search}
          onChange={(event) => setSearch(event.target.value)}
          className="max-w-md border-[#dce8e3] bg-white"
        />
        <Select value={source} onValueChange={(value) => setSource(value || "all")}>
          <SelectTrigger className="max-w-[220px] border-[#dce8e3] bg-white">
            <SelectValue placeholder="Source" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="all">All sources</SelectItem>
            {sources.map((item) => (
              <SelectItem key={item} value={item}>
                {item}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
      </section>

      <section className="page-enter grid gap-4 md:grid-cols-2 xl:grid-cols-3">
        {filteredSuppliers.map((supplier) => (
          <Card key={supplier.id} className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
            <CardHeader className="flex flex-row items-start justify-between gap-4">
              <div>
                <CardTitle className="text-lg">{supplier.name}</CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">
                  {supplier.location || "Unknown"} - {supplier.source}
                </p>
              </div>
              <div className="text-right">
                <p className={`text-3xl font-semibold ${getTrustColor(supplier.trust_score)}`}>
                  {supplier.trust_score}%
                </p>
                <p className="text-xs text-muted-foreground">trust</p>
              </div>
            </CardHeader>
            <CardContent className="space-y-4">
              <div className="grid grid-cols-3 gap-3 text-sm">
                <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-3 text-center">
                  <p className="font-semibold">{supplier.total_listings.toLocaleString()}</p>
                  <p className="text-xs text-muted-foreground">Listings</p>
                </div>
                <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-3 text-center">
                  <p className="font-semibold">{naira(supplier.avg_price)}</p>
                  <p className="text-xs text-muted-foreground">Avg price</p>
                </div>
                <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-3 text-center">
                  <p className={`font-semibold ${supplier.suspicious_count > 0 ? "text-[#c2413a]" : "text-[#166534]"}`}>
                    {supplier.suspicious_count}
                  </p>
                  <p className="text-xs text-muted-foreground">Flagged</p>
                </div>
              </div>
              <div>
                <div className="flex items-center justify-between text-sm">
                  <span className="text-muted-foreground">Reliability band</span>
                  <span className="font-medium">
                    {supplier.trust_score >= 90 ? "Trusted" : supplier.trust_score >= 75 ? "Watch" : "Review"}
                  </span>
                </div>
                <div className="mt-2 h-2 rounded-full bg-[#e8f2ee]">
                  <div className="h-2 rounded-full bg-[#3f8f78]" style={{ width: `${supplier.trust_score}%` }} />
                </div>
              </div>
            </CardContent>
          </Card>
        ))}
      </section>
    </WorkspaceShell>
  );
}
