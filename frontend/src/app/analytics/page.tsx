"use client";

import { Sidebar } from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { priceTrends, categoryDistribution, mockDashboardStats } from "@/lib/data/mockData";

export default function AnalyticsPage() {
  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-muted/30">
        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Analytics</h1>
            <p className="text-muted-foreground mt-1">
              Market insights and price intelligence
            </p>
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <Card>
              <CardHeader>
                <CardTitle>Price Trends Over Time</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-6">
                  {["cement", "iphone", "generator"].map((item) => {
                    const key = item as keyof typeof priceTrends[0];
                    const maxVal =
                      item === "cement"
                        ? 16000
                        : item === "iphone"
                        ? 700000
                        : 190000;
                    const color =
                      item === "cement"
                        ? "bg-primary"
                        : item === "iphone"
                        ? "bg-blue-500"
                        : "bg-green-500";

                    return (
                      <div key={item} className="space-y-2">
                        <div className="flex justify-between text-sm">
                          <span className="capitalize">{item}</span>
                          <span className="text-muted-foreground">
                            ₦{priceTrends[4][key].toLocaleString()}
                          </span>
                        </div>
                        <div className="flex gap-1 h-8">
                          {priceTrends.map((data, i) => {
                            const val = data[key] as number;
                            const height = (val / maxVal) * 100;
                            return (
                              <div
                                key={i}
                                className={`${color} rounded flex-1 opacity-80 hover:opacity-100 transition-opacity`}
                                style={{ height: `${height}%` }}
                                title={`${data.month}: ₦${val.toLocaleString()}`}
                              />
                            );
                          })}
                        </div>
                        <div className="flex justify-between text-xs text-muted-foreground">
                          <span>Jan</span>
                          <span>May</span>
                        </div>
                      </div>
                    );
                  })}
                </div>
              </CardContent>
            </Card>

            <Card>
              <CardHeader>
                <CardTitle>Category Breakdown</CardTitle>
              </CardHeader>
              <CardContent className="space-y-6">
                {categoryDistribution.map((cat, index) => {
                  const colors = [
                    "bg-primary",
                    "bg-blue-500",
                    "bg-green-500",
                    "bg-orange-500",
                    "bg-purple-500",
                  ];
                  return (
                    <div key={cat.name} className="space-y-2">
                      <div className="flex justify-between text-sm">
                        <span>{cat.name}</span>
                        <span className="font-medium">{cat.value}%</span>
                      </div>
                      <div className="h-6 bg-muted rounded-full overflow-hidden">
                        <div
                          className={`h-full ${colors[index]} rounded-full`}
                          style={{ width: `${cat.value}%` }}
                        />
                      </div>
                    </div>
                  );
                })}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader>
                <CardTitle>Key Metrics</CardTitle>
              </CardHeader>
              <CardContent>
                <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                  <div className="p-4 rounded-lg border text-center">
                    <p className="text-3xl font-bold">
                      {mockDashboardStats.totalListings}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Total Listings
                    </p>
                  </div>
                  <div className="p-4 rounded-lg border text-center">
                    <p className="text-3xl font-bold">
                      {mockDashboardStats.suspiciousPrices}
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Suspicious Prices
                    </p>
                  </div>
                  <div className="p-4 rounded-lg border text-center">
                    <p className="text-3xl font-bold">
                      {mockDashboardStats.totalSuppliers}
                    </p>
                    <p className="text-sm text-muted-foreground">Suppliers</p>
                  </div>
                  <div className="p-4 rounded-lg border text-center">
                    <p className="text-3xl font-bold">
                      {mockDashboardStats.avgTrustScore}%
                    </p>
                    <p className="text-sm text-muted-foreground">
                      Avg Trust Score
                    </p>
                  </div>
                </div>
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}