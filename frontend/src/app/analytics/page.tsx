"use client";

import { useEffect, useMemo, useState } from "react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CategoryBreakdown, DashboardSummary, ProductSummary, fetchJson } from "@/lib/api";

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(value);
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [categories, setCategories] = useState<CategoryBreakdown[]>([]);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    async function loadAnalytics() {
      setIsLoading(true);
      setError("");
      try {
        const [summaryData, categoryData, productData] = await Promise.all([
          fetchJson<DashboardSummary>("/api/analytics/summary"),
          fetchJson<CategoryBreakdown[]>("/api/analytics/categories"),
          fetchJson<ProductSummary[]>("/api/products/?limit=8"),
        ]);
        setSummary(summaryData);
        setCategories(categoryData);
        setProducts(productData);
      } catch (caught) {
        setSummary(null);
        setCategories([]);
        setProducts([]);
        setError(caught instanceof Error ? caught.message : "Could not load analytics");
      } finally {
        setIsLoading(false);
      }
    }

    loadAnalytics();
  }, [reloadToken]);

  const totalCategoryCount = categories.reduce((total, item) => total + item.count, 0);
  const maxListings = useMemo(() => Math.max(...products.map((product) => product.listings_count), 1), [products]);

  return (
    <WorkspaceShell>
      <section className="page-enter flex flex-col gap-2">
        <span className="metric-pill w-fit">Benchmark intelligence</span>
        <h1 className="text-4xl font-semibold tracking-tight text-[#173b39]">Analytics and benchmark view</h1>
        <p className="max-w-3xl text-sm text-[#48655d]">Read market coverage, category mix, detected price flags, and source-trust state from persisted data.</p>
      </section>

      {isLoading ? (
        <StatusCard title="Loading analytics" body="Reading persisted market summaries from the API." />
      ) : error || !summary ? (
        <StatusCard
          title="Analytics unavailable"
          body={error || "The API returned an incomplete analytics state. Metrics are not being replaced with zeros."}
          error
          action={<Button variant="outline" onClick={() => setReloadToken((value) => value + 1)}>Retry</Button>}
        />
      ) : (
        <>
          <section className="page-enter grid gap-4 md:grid-cols-4">
            <Metric label="Products" value={summary.total_products.toLocaleString()} />
            <Metric label="Suppliers" value={summary.total_suppliers.toLocaleString()} />
            <Metric label="Listings" value={summary.total_listings.toLocaleString()} />
            <Metric label="Detected flags" value={summary.suspicious_prices.toLocaleString()} warning />
          </section>

          <section className="page-enter grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
            <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader><CardTitle className="text-lg">Product observation coverage</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {products.map((product) => (
                  <div key={product.id} className="space-y-2">
                    <div className="flex items-center justify-between gap-4 text-sm">
                      <div><p className="font-medium text-[#173b39]">{product.name}</p><p className="text-muted-foreground">{product.category || "Uncategorized"} - {product.listings_count} listings</p></div>
                      <span className="font-semibold">{naira(product.avg_price)}</span>
                    </div>
                    <div className="h-3 rounded-full bg-[#e8f2ee]"><div className="h-3 rounded-full bg-[#3f8f78]" style={{ width: `${(product.listings_count / maxListings) * 100}%` }} /></div>
                  </div>
                ))}
                {!products.length ? <p className="text-sm text-muted-foreground">No canonical product observations yet.</p> : null}
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader><CardTitle className="text-lg">Market health</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                <HealthMetric label="Average supplier trust" value={`${summary.avg_trust_score}%`} />
                <HealthMetric label="Detected-flag ratio" value={summary.total_listings ? `${Math.round((summary.suspicious_prices / summary.total_listings) * 100)}%` : "No listings"} warning />
                <HealthMetric label="Review signal" value={summary.total_listings === 0 ? "No data" : summary.suspicious_prices === 0 ? "No detected flags" : "Review flags"} />
              </CardContent>
            </Card>
          </section>

          <section className="page-enter grid gap-6 lg:grid-cols-2">
            <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader><CardTitle className="text-lg">Category mix</CardTitle></CardHeader>
              <CardContent className="space-y-4">
                {categories.map((item) => {
                  const percentage = totalCategoryCount ? Math.round((item.count / totalCategoryCount) * 100) : 0;
                  return (
                    <div key={item.category} className="space-y-2">
                      <div className="flex items-center justify-between text-sm"><span>{item.category}</span><span className="text-muted-foreground">{percentage}%</span></div>
                      <div className="h-3 rounded-full bg-[#e8f2ee]"><div className="h-3 rounded-full bg-[#3f8f78]" style={{ width: `${percentage}%` }} /></div>
                    </div>
                  );
                })}
                {!categories.length ? <p className="text-sm text-muted-foreground">No category data yet.</p> : null}
              </CardContent>
            </Card>

            <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader><CardTitle className="text-lg">How to read this view</CardTitle></CardHeader>
              <CardContent className="space-y-4 text-sm text-[#48655d]">
                <p>Observed averages come from linked raw listings. Benchmark recalculation is a separate operation and persists its own price history.</p>
                <p>Extreme price outliers become explicit review records; they are excluded from benchmark calculation but remain visible for analyst inspection.</p>
                <p>This screen reports data state only. It does not imply publication approval or production release readiness.</p>
              </CardContent>
            </Card>
          </section>
        </>
      )}
    </WorkspaceShell>
  );
}

function Metric({ label, value, warning = false }: { label: string; value: string; warning?: boolean }) {
  return <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardContent className="p-5"><p className="text-sm text-muted-foreground">{label}</p><p className={`mt-2 text-3xl font-semibold ${warning ? "text-[#b45309]" : "text-[#173b39]"}`}>{value}</p></CardContent></Card>;
}

function HealthMetric({ label, value, warning = false }: { label: string; value: string; warning?: boolean }) {
  return <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4"><p className="text-sm text-muted-foreground">{label}</p><p className={`mt-2 text-2xl font-semibold ${warning ? "text-[#b45309]" : "text-[#173b39]"}`}>{value}</p></div>;
}

function StatusCard({ title, body, action, error = false }: { title: string; body: string; action?: React.ReactNode; error?: boolean }) {
  return <Card className={`page-enter rounded-2xl shadow-none ${error ? "border-red-200 bg-red-50" : "border-[#dce8e3] bg-white"}`}><CardContent className="flex flex-wrap items-center justify-between gap-4 p-6"><div><p className={`font-semibold ${error ? "text-red-800" : "text-[#173b39]"}`}>{title}</p><p className={`mt-1 text-sm ${error ? "text-red-700" : "text-[#48655d]"}`}>{body}</p></div>{action}</CardContent></Card>;
}
