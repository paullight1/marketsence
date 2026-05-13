"use client";

import { AlertTriangle, Package, TrendingUp, Users } from "lucide-react";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { DashboardSummary } from "@/lib/api";

type StatsCardsProps = {
  summary?: DashboardSummary | null;
};

export function StatsCards({ summary }: StatsCardsProps) {
  const stats = [
    {
      title: "Total Products",
      value: summary?.total_products ?? 0,
      icon: Package,
      description: "Normalized products",
    },
    {
      title: "Suppliers",
      value: summary?.total_suppliers ?? 0,
      icon: Users,
      description: "Live supplier records",
    },
    {
      title: "Suspicious Prices",
      value: summary?.suspicious_prices ?? 0,
      icon: AlertTriangle,
      description: "Flagged listings",
      alert: true,
    },
    {
      title: "Avg Trust Score",
      value: `${summary?.avg_trust_score ?? 0}%`,
      icon: TrendingUp,
      description: "Supplier reliability",
    },
  ];

  return (
    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4">
      {stats.map((stat) => (
        <Card key={stat.title} className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">{stat.title}</CardTitle>
            <stat.icon className={`size-4 ${stat.alert ? "text-[#c2413a]" : "text-[#3f8f78]"}`} />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{typeof stat.value === "number" ? stat.value.toLocaleString() : stat.value}</div>
            <p className="mt-1 text-xs text-muted-foreground">{stat.description}</p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}
