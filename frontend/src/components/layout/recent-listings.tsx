"use client";

import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OpsRecentListing } from "@/lib/api";

type RecentListingsProps = {
  listings?: OpsRecentListing[];
};

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", {
    style: "currency",
    currency: "NGN",
    maximumFractionDigits: 0,
  }).format(value);
}

export function RecentListings({ listings = [] }: RecentListingsProps) {
  return (
    <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
      <CardHeader>
        <CardTitle>Recent Price Listings</CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          {listings.slice(0, 5).map((listing) => (
            <div key={listing.id} className="flex items-center justify-between rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-3">
              <div className="space-y-1">
                <p className="text-sm font-medium">{listing.product_name}</p>
                <p className="text-xs text-muted-foreground">
                  {listing.seller} - {listing.location || "Unknown"}
                </p>
              </div>
              <div className="text-right">
                <p className="font-semibold">{naira(listing.price)}</p>
                <Badge variant="secondary" className="text-xs">
                  {listing.is_suspicious ? "Flagged" : listing.source}
                </Badge>
              </div>
            </div>
          ))}
          {!listings.length ? <p className="text-sm text-muted-foreground">No listings loaded.</p> : null}
        </div>
      </CardContent>
    </Card>
  );
}
