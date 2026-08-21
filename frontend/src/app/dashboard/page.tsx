"use client";

import type { ReactNode } from "react";
import { useEffect, useState } from "react";
import { AlertTriangle, Database, RefreshCcw, ShieldCheck } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
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
  const [isLoading, setIsLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    async function loadDashboard() {
      setIsLoading(true);
      setError("");
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
        setSummary(null);
        setOps(null);
        setProducts([]);
        setSuppliers([]);
        setError(caught instanceof Error ? caught.message : "Could not load dashboard data");
      } finally {
        setIsLoading(false);
      }
    }

    loadDashboard();
  }, [reloadToken]);

  const ready = summary !== null && ops !== null;
  const unresolvedMetric = ops?.queue_metrics.find((metric) => metric.label === "Unresolved matches");

  return (
    <WorkspaceShell>
      <section className="page-enter overflow-hidden rounded-2xl border border-[#dce8e3] bg-white">
        <div className="border-b border-[#dce8e3] bg-[#f4faf7] p-7">
          <div className="flex flex-wrap items-center gap-3">
            <span className="metric-pill">Live backend data</span>
            <span className="metric-pill">Evidence-backed status</span>
          </div>
          <h1 className="mt-5 max-w-3xl text-4xl font-semibold tracking-tight text-[#173b39]">
            Nigerian market intelligence from raw data to benchmark.
          </h1>
          <p className="mt-3 max-w-2xl text-sm leading-6 text-[#48655d]">
            Listings, suppliers, products, unresolved matches, benchmark state, and review pressure are read from the FastAPI data layer.
          </p>
        </div>
      </section>

      {isLoading ? (
        <StateCard title="Loading market state" body="Reading analytics, operations, products, and suppliers from the API." />
      ) : error || !ready ? (
        <StateCard
          title="Market data unavailable"
          body={error || "The API did not return a complete dashboard state. No zero values are being substituted."}
          action={<Button variant="outline" onClick={() => setReloadToken((value) => value + 1)}>Retry</Button>}
          error
        />
      ) : (
        <>
          <section className="page-enter grid gap-6 lg:grid-cols-[1.35fr_0.95fr]">
            <div className="grid gap-4 rounded-2xl border border-[#dce8e3] bg-white p-5 md:grid-cols-2 xl:grid-cols-4">
              <MetricCard title="Products" value={summary.total_products} icon={<Database className="size-4 text-[#3f8f78]" />} />
              <MetricCard title="Suppliers" value={summary.total_suppliers} icon={<ShieldCheck className="size-4 text-[#3f8f78]" />} />
              <MetricCard title="Raw listings" value={summary.total_listings} icon={<RefreshCcw className="size-4 text-[#3f8f78]" />} />
              <MetricCard title="Detected flags" value={summary.suspicious_prices} icon={<AlertTriangle className="size-4 text-[#c2413a]" />} />
            </div>

            <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader><CardTitle className="text-lg">Queue health</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {ops.queue_metrics.map((metric) => (
                  <div key={metric.label} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                    <p className="text-sm text-muted-foreground">{metric.label}</p>
                    <p className={`mt-2 text-3xl font-semibold ${metric.tone === "warning" ? "text-[#b45309]" : "text-[#173b39]"}`}>{metric.value}</p>
                  </div>
                ))}
              </CardContent>
            </Card>
          </section>

          <section className="page-enter grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
            <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-lg">Pipeline state</CardTitle>
                <span className="metric-pill">{ops.tasks.length} tracked stages</span>
              </CardHeader>
              <CardContent className="grid gap-4">
                {ops.tasks.map((task) => (
                  <div key={task.id} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                    <div className="flex flex-wrap items-center justify-between gap-3">
                      <div>
                        <p className="text-base font-semibold">{task.title}</p>
                        <p className="text-sm text-muted-foreground">{task.owner} - {task.source}</p>
                      </div>
                      <span className="metric-pill">{task.stage}</span>
                    </div>
                    <div className="mt-4 h-2 rounded-full bg-[#e8f2ee]"><div className="h-2 rounded-full bg-[#3f8f78]" style={{ width: `${task.progress}%` }} /></div>
                    <div className="mt-3 flex flex-wrap items-center justify-between gap-2 text-sm text-muted-foreground"><span>{task.listings.toLocaleString()} records</span><span>{task.eta}</span></div>
                    <p className="mt-2 text-sm text-[#48655d]">{task.note}</p>
                  </div>
                ))}
              </CardContent>
            </Card>

            <div className="grid gap-6">
              <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
                <CardHeader><CardTitle className="text-lg">Review pressure</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                    <p className="text-sm text-muted-foreground">Unresolved matching queue</p>
                    <p className="mt-2 text-3xl font-semibold text-[#173b39]">{unresolvedMetric?.value ?? "0"}</p>
                  </div>
                  {ops.review_alerts.map((alert) => (
                    <div key={alert.id} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                      <p className="font-semibold">{alert.product}</p>
                      <p className="text-sm text-muted-foreground">{alert.issue}</p>
                      <p className="mt-2 text-sm text-[#b45309]">{alert.severity}</p>
                    </div>
                  ))}
                  {!ops.review_alerts.length ? <p className="text-sm text-muted-foreground">No records are currently waiting in the review feed.</p> : null}
                </CardContent>
              </Card>

              <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
                <CardHeader><CardTitle className="text-lg">Recent listings</CardTitle></CardHeader>
                <CardContent className="space-y-3">
                  {ops.recent_listings.map((listing) => (
                    <div key={listing.id} className="flex items-center justify-between rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                      <div><p className="font-semibold">{listing.product_name}</p><p className="text-sm text-muted-foreground">{listing.seller} - {listing.location || "Unknown"}</p></div>
                      <div className="text-right"><p className="font-semibold">{naira(listing.price)}</p><p className={`text-sm ${listing.is_suspicious ? "text-[#c2413a]" : "text-[#166534]"}`}>{listing.is_suspicious ? "Flagged" : listing.source}</p></div>
                    </div>
                  ))}
                  {!ops.recent_listings.length ? <p className="text-sm text-muted-foreground">No listings have been ingested yet.</p> : null}
                </CardContent>
              </Card>
            </div>
          </section>

          <section className="page-enter grid gap-6 lg:grid-cols-2">
            <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader><CardTitle className="text-lg">Top products from API</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {products.map((product) => (
                  <div key={product.id} className="flex items-center justify-between rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                    <div><p className="font-semibold">{product.name}</p><p className="text-sm text-muted-foreground">{product.category || "Uncategorized"} - {product.brand || "No brand"}</p></div>
                    <div className="text-right"><p className="font-semibold">{naira(product.avg_price)}</p><p className="text-sm text-muted-foreground">{product.listings_count} listings</p></div>
                  </div>
                ))}
                {!products.length ? <p className="text-sm text-muted-foreground">No canonical products yet.</p> : null}
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader><CardTitle className="text-lg">Supplier trust from API</CardTitle></CardHeader>
              <CardContent className="space-y-3">
                {suppliers.map((supplier) => (
                  <div key={supplier.id} className="flex items-center justify-between rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                    <div><p className="font-semibold">{supplier.name}</p><p className="text-sm text-muted-foreground">{supplier.source} - {supplier.location || "Unknown"}</p></div>
                    <p className="text-lg font-semibold">{supplier.trust_score}%</p>
                  </div>
                ))}
                {!suppliers.length ? <p className="text-sm text-muted-foreground">No suppliers yet.</p> : null}
              </CardContent>
            </Card>
          </section>
        </>
      )}
    </WorkspaceShell>
  );
}

function MetricCard({ title, value, icon }: { title: string; value: number; icon: ReactNode }) {
  return (
    <Card className="rounded-xl border-[#dce8e3] bg-[#fbfefd] shadow-none">
      <CardHeader className="pb-2"><CardTitle className="flex items-center justify-between text-sm text-muted-foreground">{title}{icon}</CardTitle></CardHeader>
      <CardContent><p className="text-3xl font-semibold">{value.toLocaleString()}</p></CardContent>
    </Card>
  );
}

function StateCard({ title, body, action, error = false }: { title: string; body: string; action?: ReactNode; error?: boolean }) {
  return (
    <Card className={`page-enter rounded-2xl shadow-none ${error ? "border-red-200 bg-red-50" : "border-[#dce8e3] bg-white"}`}>
      <CardContent className="flex flex-wrap items-center justify-between gap-4 p-6">
        <div><p className={`font-semibold ${error ? "text-red-800" : "text-[#173b39]"}`}>{title}</p><p className={`mt-1 text-sm ${error ? "text-red-700" : "text-[#48655d]"}`}>{body}</p></div>
        {action}
      </CardContent>
    </Card>
  );
}
