"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { AlertTriangle, Database, RefreshCcw, ShieldCheck } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  DashboardSummary,
  OpsOverview,
  ProductSummary,
  SupplierSummary,
  fetchJson,
} from "@/lib/api";

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function DashboardPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [ops, setOps] = useState<OpsOverview | null>(null);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [suppliers, setSuppliers] = useState<SupplierSummary[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        const [summaryData, opsData, productData, supplierData] = await Promise.all([
          fetchJson<DashboardSummary>("/api/analytics/summary"),
          fetchJson<OpsOverview>("/api/ops/overview"),
          fetchJson<ProductSummary[]>("/api/products/?limit=6"),
          fetchJson<SupplierSummary[]>("/api/suppliers/?limit=5"),
        ]);
        setSummary(summaryData);
        setOps(opsData);
        setProducts(productData);
        setSuppliers(supplierData);
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Could not load dashboard data");
      }
    }

    loadDashboard();
  }, []);

  const unresolvedMetric = ops?.queue_metrics.find((metric) => metric.label === "Unresolved matches");

  return (
    <WorkspaceShell>
      <section className="page-enter grid gap-6 lg:grid-cols-[1.35fr_0.95fr]">
        <div className="overflow-hidden rounded-2xl border border-[#dce8e3] bg-white">
          <div className="border-b border-[#dce8e3] bg-[#f4faf7] p-7">
            <div className="flex flex-wrap items-center gap-3">
              <span className="metric-pill">Live backend data</span>
              <span className="metric-pill">Scrape and CSV ingestion</span>
            </div>
            <h1 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-[#173b39]">
              Nigerian market intelligence from raw data to benchmark.
            </h1>
            <p className="mt-3 max-w-2xl text-sm leading-6 text-[#48655d]">
              This dashboard reads the FastAPI database state directly: listings, suppliers, products, unresolved matches, and review pressure.
            </p>
            {error ? (
              <p className="mt-4 rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
                {error}
              </p>
            ) : null}
          </div>
          <div className="grid gap-4 p-5 md:grid-cols-2 xl:grid-cols-4">
            <MetricCard title="Products" value={summary?.total_products ?? 0} icon={<Database className="size-4 text-[#3f8f78]" />} />
            <MetricCard title="Suppliers" value={summary?.total_suppliers ?? 0} icon={<ShieldCheck className="size-4 text-[#3f8f78]" />} />
            <MetricCard title="Raw listings" value={summary?.total_listings ?? 0} icon={<RefreshCcw className="size-4 text-[#3f8f78]" />} />
            <MetricCard title="Suspicious" value={summary?.suspicious_prices ?? 0} icon={<AlertTriangle className="size-4 text-[#c2413a]" />} />
          </div>
        </div>

        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Queue health</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {(ops?.queue_metrics ?? []).map((metric) => (
              <div key={metric.label} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                <p className="text-sm text-muted-foreground">{metric.label}</p>
                <p className={`mt-2 text-3xl font-semibold ${metric.tone === "warning" ? "text-[#b45309]" : "text-[#173b39]"}`}>
                  {metric.value}
                </p>
              </div>
            ))}
            {!ops ? <p className="text-sm text-muted-foreground">Loading queue metrics...</p> : null}
          </CardContent>
        </Card>
      </section>

      <section className="page-enter grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader className="flex flex-row items-center justify-between">
            <CardTitle className="text-lg">Active task board</CardTitle>
            <span className="metric-pill">{ops?.tasks.length ?? 0} tracked jobs</span>
          </CardHeader>
          <CardContent className="grid gap-4">
            {(ops?.tasks ?? []).map((task) => (
              <div key={task.id} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                <div className="flex flex-wrap items-center justify-between gap-3">
                  <div>
                    <p className="text-base font-semibold">{task.title}</p>
                    <p className="text-sm text-muted-foreground">{task.owner} - {task.source}</p>
                  </div>
                  <span className="metric-pill">{task.stage}</span>
                </div>
                <div className="mt-4 h-2 rounded-full bg-[#e8f2ee]">
                  <div className="h-2 rounded-full bg-[#3f8f78]" style={{ width: `${task.progress}%` }} />
                </div>
                <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-sm text-muted-foreground">
                  <span>{task.listings.toLocaleString()} records</span>
                  <span>{task.eta}</span>
                </div>
                <p className="mt-2 text-sm text-[#48655d]">{task.note}</p>
              </div>
            ))}
          </CardContent>
        </Card>

        <div className="grid gap-6">
          <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
            <CardHeader>
              <CardTitle className="text-lg">Review pressure</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                <p className="text-sm text-muted-foreground">Unresolved matching queue</p>
                <p className="mt-2 text-3xl font-semibold text-[#173b39]">
                  {unresolvedMetric?.value ?? "0"}
                </p>
              </div>
              {(ops?.review_alerts ?? []).map((alert) => (
                <div key={alert.id} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                  <p className="font-semibold">{alert.product}</p>
                  <p className="text-sm text-muted-foreground">{alert.issue}</p>
                  <p className="mt-2 text-sm text-[#b45309]">{alert.severity}</p>
                </div>
              ))}
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
            <CardHeader>
              <CardTitle className="text-lg">Recent listings</CardTitle>
            </CardHeader>
            <CardContent className="space-y-3">
              {(ops?.recent_listings ?? []).map((listing) => (
                <div key={listing.id} className="flex items-center justify-between rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                  <div>
                    <p className="font-semibold">{listing.product_name}</p>
                    <p className="text-sm text-muted-foreground">{listing.seller} - {listing.location || "Unknown"}</p>
                  </div>
                  <div className="text-right">
                    <p className="font-semibold">{naira(listing.price)}</p>
                    <p className={`text-sm ${listing.is_suspicious ? "text-[#c2413a]" : "text-[#166534]"}`}>
                      {listing.is_suspicious ? "Flagged" : listing.source}
                    </p>
                  </div>
                </div>
              ))}
            </CardContent>
          </Card>
        </div>
      </section>

      <section className="page-enter grid gap-6 lg:grid-cols-2">
        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Top products from API</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {products.map((product) => (
              <div key={product.id} className="flex items-center justify-between rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                <div>
                  <p className="font-semibold">{product.name}</p>
                  <p className="text-sm text-muted-foreground">{product.category || "Uncategorized"} - {product.brand || "No brand"}</p>
                </div>
                <div className="text-right">
                  <p className="font-semibold">{naira(product.avg_price)}</p>
                  <p className="text-sm text-muted-foreground">{product.listings_count} listings</p>
                </div>
              </div>
            ))}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Supplier trust from API</CardTitle>
          </CardHeader>
          <CardContent className="space-y-3">
            {suppliers.map((supplier) => (
              <div key={supplier.id} className="flex items-center justify-between rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                <div>
                  <p className="font-semibold">{supplier.name}</p>
                  <p className="text-sm text-muted-foreground">{supplier.source} - {supplier.location || "Unknown"}</p>
                </div>
                <p className="text-lg font-semibold">{supplier.trust_score}%</p>
              </div>
            ))}
          </CardContent>
        </Card>
      </section>
    </WorkspaceShell>
  );
}

function MetricCard({ title, value, icon }: { title: string; value: number; icon: ReactNode }) {
  return (
    <Card className="rounded-xl border-[#dce8e3] bg-[#fbfefd] shadow-none">
      <CardHeader className="pb-2">
        <CardTitle className="flex items-center justify-between text-sm text-muted-foreground">
          {title}
          {icon}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <p className="text-3xl font-semibold">{value.toLocaleString()}</p>
      </CardContent>
    </Card>
  );
}
