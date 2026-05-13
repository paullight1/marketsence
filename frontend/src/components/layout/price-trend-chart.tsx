"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductSummary } from "@/lib/api";

type PriceTrendChartProps = {
  products?: ProductSummary[];
};

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 0,
  }).format(value);
}

export function PriceTrendChart({ products = [] }: PriceTrendChartProps) {
  const maxPrice = Math.max(...products.map((product) => product.avg_price), 1);

  return (
    <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
      <CardHeader>
        <CardTitle>Price Benchmark Snapshot</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="flex h-[260px] items-end justify-between gap-4 px-2">
          {products.slice(0, 8).map((product) => (
            <div key={product.id} className="flex min-w-0 flex-1 flex-col items-center gap-2">
              <div
                className="w-full max-w-12 rounded-t-xl bg-[#3f8f78]"
                style={{ height: `${Math.max((product.avg_price / maxPrice) * 100, 4)}%` }}
                title={`${product.name}: ${naira(product.avg_price)}`}
              />
              <span className="w-full truncate text-center text-xs text-muted-foreground">{product.name}</span>
            </div>
          ))}
        </div>
        {!products.length ? <p className="text-sm text-muted-foreground">No product prices loaded.</p> : null}
      </CardContent>
    </Card>
  );
}
