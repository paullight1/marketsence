"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { CategoryBreakdown } from "@/lib/api";

type CategoryChartProps = {
  categories?: CategoryBreakdown[];
};

export function CategoryChart({ categories = [] }: CategoryChartProps) {
  const total = categories.reduce((acc, item) => acc + item.count, 0);

  return (
    <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
      <CardHeader>
        <CardTitle>Category Distribution</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {categories.map((category) => {
          const percentage = total ? Math.round((category.count / total) * 100) : 0;
          return (
            <div key={category.category} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>{category.category}</span>
                <span className="text-muted-foreground">{percentage}%</span>
              </div>
              <div className="h-2 overflow-hidden rounded-full bg-[#e8f2ee]">
                <div className="h-full rounded-full bg-[#3f8f78]" style={{ width: `${percentage}%` }} />
              </div>
            </div>
          );
        })}
        {!categories.length ? <p className="text-sm text-muted-foreground">No categories loaded.</p> : null}
      </CardContent>
    </Card>
  );
}
