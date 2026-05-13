"use client";

import { useEffect, useMemo, useState } from "react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  CategoryBreakdown,
  DashboardSummary,
  ProductSummary,
  fetchJson,
} from "@/lib/api";

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 0,
  }).format(value);
}

export default function AnalyticsPage() {
  const [summary, setSummary] = useState<DashboardSummary | null>(null);
  const [categories, setCategories] = useState<CategoryBreakdown[]>([]);
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadAnalytics() {
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
        setError(caught instanceof Error ? caught.message : "Could not load analytics");
      }
    }

    loadAnalytics();
  }, []);

  const totalCategoryCount = categories.reduce((total, item) => total + item.count, 0);
  const maxListings = useMemo(
    () => Math.max(...products.map((product) => product.listings_count), 1),
    [products],
  );

  return (
    <WorkspaceShell>
      <section className="page-enter flex flex-col gap-2">
        <span className="metric-pill w-fit">Benchmark intelligence</span>
        <h1 className="text-4xl font-semibold tracking-tight text-[#173b39]">
          Analytics and benchmark view
        </h1>
        <p className="max-w-3xl text-sm text-[#48655d]">
          Read live market coverage, category mix, suspicious-price pressure, and benchmark readiness from your database.
        </p>
        {error ? (
          <p className="w-fit rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}
      </section>

      <section className="page-enter grid gap-4 md:grid-cols-4">
        <Metric label="Products" value={(summary?.total_products ?? 0).toLocaleString()} />
        <Metric label="Suppliers" value={(summary?.total_suppliers ?? 0).toLocaleString()} />
        <Metric label="Listings" value={(summary?.total_listings ?? 0).toLocaleString()} />
        <Metric label="Suspicious" value={(summary?.suspicious_prices ?? 0).toLocaleString()} warning />
      </section>

      <section className="page-enter grid gap-6 lg:grid-cols-[1.25fr_0.75fr]">
        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Product benchmark coverage</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {products.map((product) => (
              <div key={product.id} className="space-y-2">
                <div className="flex items-center justify-between gap-4 text-sm">
                  <div>
                    <p className="font-medium text-[#173b39]">{product.name}</p>
                    <p className="text-muted-foreground">
                      {product.category || "Uncategorized"} - {product.listings_count} listings
                    </p>
                  </div>
                  <span className="font-semibold">{naira(product.avg_price)}</span>
                </div>
                <div className="h-3 rounded-full bg-[#e8f2ee]">
                  <div
                    className="h-3 rounded-full bg-[#3f8f78]"
                    style={{ width: `${(product.listings_count / maxListings) * 100}%` }}
                  />
                </div>
              </div>
            ))}
            {!products.length ? <p className="text-sm text-muted-foreground">No product benchmarks yet.</p> : null}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Market health</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
              <p className="text-sm text-muted-foreground">Average supplier trust</p>
              <p className="mt-2 text-3xl font-semibold">{summary?.avg_trust_score ?? 0}%</p>
            </div>
            <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
              <p className="text-sm text-muted-foreground">Review ratio</p>
              <p className="mt-2 text-3xl font-semibold text-[#b45309]">
                {summary?.total_listings
                  ? `${Math.round(((summary.suspicious_prices || 0) / summary.total_listings) * 100)}%`
                  : "0%"}
              </p>
            </div>
            <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
              <p className="text-sm text-muted-foreground">Publish readiness</p>
              <p className="mt-2 text-3xl font-semibold text-[#166534]">
                {(summary?.suspicious_prices ?? 0) === 0 ? "Clear" : "Review"}
              </p>
            </div>
          </CardContent>
        </Card>
      </section>

      <section className="page-enter grid gap-6 lg:grid-cols-2">
        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Category mix</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4">
            {categories.map((item) => {
              const percentage = totalCategoryCount ? Math.round((item.count / totalCategoryCount) * 100) : 0;
              return (
                <div key={item.category} className="space-y-2">
                  <div className="flex items-center justify-between text-sm">
                    <span>{item.category}</span>
                    <span className="text-muted-foreground">{percentage}%</span>
                  </div>
                  <div className="h-3 rounded-full bg-[#e8f2ee]">
                    <div className="h-3 rounded-full bg-[#3f8f78]" style={{ width: `${percentage}%` }} />
                  </div>
                </div>
              );
            })}
            {!categories.length ? <p className="text-sm text-muted-foreground">No category data yet.</p> : null}
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Interpretation</CardTitle>
          </CardHeader>
          <CardContent className="space-y-4 text-sm text-[#48655d]">
            <p>Analytics should never depend on invented frontend records. This page now reads the same backend tables used by ingestion, normalization, and reviews.</p>
            <p>When the dataset grows, this view should move from direct live reads to cached summaries so the dashboard stays fast while jobs continue running.</p>
            <p>Suspicious records should remain reviewable until a human approves or rejects the rule that flagged them.</p>
          </CardContent>
        </Card>
      </section>
    </WorkspaceShell>
  );
}

function Metric({ label, value, warning = false }: { label: string; value: string; warning?: boolean }) {
  return (
    <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
      <CardContent className="p-5">
        <p className="text-sm text-muted-foreground">{label}</p>
        <p className={`mt-2 text-3xl font-semibold ${warning ? "text-[#b45309]" : "text-[#173b39]"}`}>
          {value}
        </p>
      </CardContent>
    </Card>
  );
}
