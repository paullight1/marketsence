"use client";

import { useState } from "react";
import { Sidebar } from "@/components/layout/sidebar";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { mockSuppliers, sources, locations } from "@/lib/data/mockData";

function getTrustColor(score: number): string {
  if (score >= 90) return "text-green-500";
  if (score >= 70) return "text-yellow-500";
  return "text-red-500";
}

export default function SuppliersPage() {
  const [search, setSearch] = useState("");
  const [source, setSource] = useState("all");

  const filteredSuppliers = mockSuppliers.filter((supplier) => {
    const matchesSearch = supplier.name
      .toLowerCase()
      .includes(search.toLowerCase());
    const matchesSource = source === "all" || supplier.source === source;
    return matchesSearch && matchesSource;
  });

  return (
    <div className="flex h-screen">
      <Sidebar />
      <main className="flex-1 overflow-y-auto bg-muted/30">
        <div className="p-6 space-y-6">
          <div>
            <h1 className="text-3xl font-bold">Suppliers</h1>
            <p className="text-muted-foreground mt-1">
              Seller trust scores and performance metrics
            </p>
          </div>

          <div className="flex gap-4">
            <Input
              placeholder="Search suppliers..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="max-w-md"
            />
            <Select value={source} onValueChange={(v) => setSource(v || "all")}>
              <SelectTrigger className="max-w-[200px]">
                <SelectValue placeholder="Source" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="all">All Sources</SelectItem>
                {sources.map((src) => (
                  <SelectItem key={src} value={src}>
                    {src}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {filteredSuppliers.map((supplier) => (
              <Card key={supplier.id}>
                <CardHeader className="flex flex-row items-center justify-between">
                  <div>
                    <CardTitle className="text-lg">{supplier.name}</CardTitle>
                    <p className="text-sm text-muted-foreground">
                      {supplier.location} • {supplier.source}
                    </p>
                  </div>
                  <div className="text-right">
                    <p
                      className={`text-2xl font-bold ${getTrustColor(
                        supplier.trustScore
                      )}`}
                    >
                      {supplier.trustScore}%
                    </p>
                    <p className="text-xs text-muted-foreground">Trust Score</p>
                  </div>
                </CardHeader>
                <CardContent>
                  <div className="grid grid-cols-3 gap-4 text-sm">
                    <div className="text-center p-2 rounded bg-muted">
                      <p className="font-semibold">{supplier.totalListings}</p>
                      <p className="text-xs text-muted-foreground">Listings</p>
                    </div>
                    <div className="text-center p-2 rounded bg-muted">
                      <p className="font-semibold">
                        ₦{(supplier.avgPrice / 1000).toFixed(0)}k
                      </p>
                      <p className="text-xs text-muted-foreground">Avg Price</p>
                    </div>
                    <div className="text-center p-2 rounded bg-muted">
                      <p
                        className={`font-semibold ${
                          supplier.suspiciousCount > 0
                            ? "text-destructive"
                            : "text-green-500"
                        }`}
                      >
                        {supplier.suspiciousCount}
                      </p>
                      <p className="text-xs text-muted-foreground">Suspicious</p>
                    </div>
                  </div>
                  <div className="mt-4">
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div
                        className={`h-full rounded-full ${
                          supplier.trustScore >= 90
                            ? "bg-green-500"
                            : supplier.trustScore >= 70
                            ? "bg-yellow-500"
                            : "bg-red-500"
                        }`}
                        style={{ width: `${supplier.trustScore}%` }}
                      />
                    </div>
                  </div>
                </CardContent>
              </Card>
            ))}
          </div>
        </div>
      </main>
    </div>
  );
}