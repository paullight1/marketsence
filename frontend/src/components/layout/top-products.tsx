"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { ProductSummary } from "@/lib/api";

type TopProductsProps = {
  products?: ProductSummary[];
};

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 0,
  }).format(value);
}

export function TopProducts({ products = [] }: TopProductsProps) {
  return (
    <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
      <CardHeader>
        <CardTitle>Top Monitored Products</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {products.slice(0, 5).map((product) => (
            <div key={product.id} className="flex items-center justify-between rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-3">
              <div className="space-y-1">
                <p className="text-sm font-medium">{product.name}</p>
                <Badge variant="outline" className="text-xs">
                  {product.category || "Uncategorized"}
                </Badge>
              </div>
              <div className="text-right">
                <p className="font-semibold">{naira(product.avg_price)}</p>
                <p className="text-xs text-muted-foreground">{product.listings_count} listings</p>
              </div>
            </div>
          ))}
          {!products.length ? <p className="text-sm text-muted-foreground">No products loaded.</p> : null}
        </div>
      </CardContent>
    </Card>
  );
}
