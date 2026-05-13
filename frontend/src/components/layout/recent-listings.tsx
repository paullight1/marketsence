"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { mockListings } from "@/lib/data/mockData";

export function RecentListings() {
  return (
    <Card>
      <CardHeader>
        <CardTitle>Recent Price Listings</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {mockListings.slice(0, 5).map((listing) => (
            <div
              key={listing.id}
              className="flex items-center justify-between p-3 rounded-lg border"
            >
              <div className="space-y-1">
                <p className="font-medium text-sm">{listing.productName}</p>
                <p className="text-xs text-muted-foreground">
                  {listing.seller} • {listing.location}
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold">₦{listing.price.toLocaleString()}</p>
                <Badge variant="secondary" className="text-xs">
                  {listing.source}
                </Badge>
              </div>
            </div>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}