"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { categoryDistribution } from "@/lib/data/mockData";

export function CategoryChart() {
  const total = categoryDistribution.reduce((acc, item) => acc + item.value, 0);

  const colors = [
    "bg-primary",
    "bg-blue-500",
    "bg-green-500",
    "bg-orange-500",
    "bg-purple-500",
  ];

  return (
    <Card>
      <CardHeader>
        <CardTitle>Category Distribution</CardTitle>
      </CardHeader>
      <CardContent className="space-y-4">
        {categoryDistribution.map((cat, index) => {
          const percentage = (cat.value / total) * 100;
          return (
            <div key={cat.name} className="space-y-2">
              <div className="flex items-center justify-between text-sm">
                <span>{cat.name}</span>
                <span className="text-muted-foreground">{cat.value}%</span>
              </div>
              <div className="h-2 bg-muted rounded-full overflow-hidden">
                <div
                  className={`h-full ${colors[index]} rounded-full transition-all`}
                  style={{ width: `${percentage}%` }}
                />
              </div>
            </div>
          );
        })}
      </CardContent>
    </Card>
  );
}