"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockProducts } from "@/lib/data/mockData";

export function TopProducts() {
  const topProducts = mockProducts.slice(0, 5);

  return (
    <Card>
      <CardHeader>
        <CardTitle>Top Monitored Products</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {topProducts.map((product) => (
            <div
              key={product.id}
              className="flex items-center justify-between p-3 rounded-lg border"
            >
              <div className="space-y-1">
                <p className="font-medium text-sm">{product.name}</p>
                <Badge variant="outline" className="text-xs">
                  {product.category}
                </Badge>
              </div>
              <div className="text-right">
                <p className="font-semibold">₦{product.avgPrice.toLocaleString()}</p>
                <p className="text-xs text-muted-foreground">
                  {product.listingsCount} listings
                </p>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}