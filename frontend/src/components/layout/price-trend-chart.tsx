"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { priceTrends } from "@/lib/data/mockData";

export function PriceTrendChart() {
  return (
    <Card className="col-span-2">
      <CardHeader>
        <CardTitle>Price Trends</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="h-[300px] flex items-end justify-between gap-4 px-4">
          {priceTrends.map((data) => (
            <div key={data.month} className="flex flex-col items-center gap-2">
              <div className="flex gap-1 items-end h-[200px]">
                <div
                  className="w-8 bg-primary/80 rounded-t"
                  style={{ height: `${(data.cement / 16000) * 100}%` }}
                  title={`Cement: ₦${data.cement.toLocaleString()}`}
                />
                <div
                  className="w-8 bg-blue-500/80 rounded-t"
                  style={{ height: `${(data.iphone / 700000) * 100}%` }}
                  title={`iPhone: ₦${data.iphone.toLocaleString()}`}
                />
                <div
                  className="w-8 bg-green-500/80 rounded-t"
                  style={{ height: `${(data.generator / 190000) * 100}%` }}
                  title={`Generator: ₦${data.generator.toLocaleString()}`}
                />
              </div>
              <span className="text-xs text-muted-foreground">{data.month}</span>
            </div>
          ))}
        </div>
        <div className="flex items-center justify-center gap-6 mt-4">
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-primary/80 rounded" />
            <span className="text-xs text-muted-foreground">Cement (50kg)</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-blue-500/80 rounded" />
            <span className="text-xs text-muted-foreground">iPhone 13 Pro Max</span>
          </div>
          <div className="flex items-center gap-2">
            <div className="w-3 h-3 bg-green-500/80 rounded" />
            <span className="text-xs text-muted-foreground">Gen 2.5KVA</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}