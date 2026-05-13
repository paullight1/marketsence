"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Package, Users, AlertTriangle, TrendingUp } from "lucide-react";
import { mockDashboardStats } from "@/lib/data/mockData";

const stats = [
  {
    title: "Total Products",
    value: mockDashboardStats.totalProducts,
    icon: Package,
    description: "Normalized products",
  },
  {
    title: "Normalization Rate",
    value: `${mockDashboardStats.normalizationRate}%`,
    icon: Users,
    description: "Fuzzy matching accuracy",
  },
  {
    title: "Suspicious Prices",
    value: mockDashboardStats.suspiciousPrices,
    icon: AlertTriangle,
    description: "Flagged listings",
    alert: true,
  },
  {
    title: "Avg Trust Score",
    value: `${mockDashboardStats.avgTrustScore}%`,
    icon: TrendingUp,
    description: "Supplier reliability",
  },
];

export function StatsCards() {
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
      {stats.map((stat) => (
        <Card key={stat.title}>
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              {stat.title}
            </CardTitle>
            <stat.icon
              className={`size-4 ${
                stat.alert ? "text-destructive" : "text-muted-foreground"
              }`}
            />
          </CardHeader>
          <CardContent>
            <div className="text-2xl font-bold">{stat.value}</div>
            <p className="text-xs text-muted-foreground mt-1">
              {stat.description}
            </p>
          </CardContent>
        </Card>
      ))}
    </div>
  );
}