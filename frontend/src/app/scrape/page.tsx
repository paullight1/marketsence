"use client";

import { FormEvent, useState } from "react";
import { Globe2, Loader2, Sparkles } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type ScrapedListing = {
  source: string;
  original_name: string;
  price: number;
  seller_name: string;
  seller_source: string;
  location: string | null;
  url: string | null;
};

type ScrapeResult = {
  scraped: number;
  ingested: number;
  listings: ScrapedListing[];
  message: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(value);
}

export default function ScrapePage() {
  const [url, setUrl] = useState("");
  const [source, setSource] = useState("Website");
  const [sellerName, setSellerName] = useState("");
  const [location, setLocation] = useState("");
  const [maxItems, setMaxItems] = useState(25);
  const [ingest, setIngest] = useState(true);
  const [result, setResult] = useState<ScrapeResult | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setResult(null);
    setIsLoading(true);

    try {
      const response = await fetch(`${apiBaseUrl}/api/ingest/scrape`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          url,
          source,
          seller_name: sellerName || null,
          seller_source: "website",
          location: location || null,
          max_items: maxItems,
          ingest,
        }),
      });

      const payload = await response.json();
      if (!response.ok) {
        throw new Error(payload.detail || "Scraping request failed");
      }

      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Scraping request failed");
    } finally {
      setIsLoading(false);
    }
  }

  return (
    <WorkspaceShell>
      <section className="page-enter grid gap-4 lg:gap-6 xl:grid-cols-[1.1fr_0.9fr]">
        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <div className="flex flex-wrap items-center gap-3">
              <span className="metric-pill">Live ingestion</span>
              <span className="metric-pill">Raw listing capture</span>
            </div>
            <CardTitle className="mt-3 text-2xl font-semibold tracking-tight text-[#173b39] sm:text-3xl">
              Scrape any target source into the pipeline
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="grid gap-4 lg:grid-cols-2">
              <label className="grid gap-2 lg:col-span-2">
                <span className="text-sm font-medium">Website URL</span>
                <Input required type="url" placeholder="https://example.com/products" value={url} onChange={(event) => setUrl(event.target.value)} className="min-w-0 border-[#dce8e3] bg-white" />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-medium">Source label</span>
                <Input value={source} onChange={(event) => setSource(event.target.value)} className="min-w-0 border-[#dce8e3] bg-white" />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-medium">Seller override</span>
                <Input placeholder="Auto from domain" value={sellerName} onChange={(event) => setSellerName(event.target.value)} className="min-w-0 border-[#dce8e3] bg-white" />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-medium">Location</span>
                <Input placeholder="Lagos" value={location} onChange={(event) => setLocation(event.target.value)} className="min-w-0 border-[#dce8e3] bg-white" />
              </label>
              <label className="grid gap-2">
                <span className="text-sm font-medium">Max items</span>
                <Input min={1} max={100} type="number" value={maxItems} onChange={(event) => setMaxItems(Number(event.target.value))} className="min-w-0 border-[#dce8e3] bg-white" />
              </label>
              <label className="flex items-start gap-3 rounded-xl border border-[#dce8e3] bg-[#fbfefd] px-4 py-3 text-sm font-medium lg:col-span-2">
                <input type="checkbox" checked={ingest} onChange={(event) => setIngest(event.target.checked)} className="mt-0.5 size-4 shrink-0 rounded border-border" />
                <span>Ingest successful results into raw listings immediately</span>
              </label>
              <div className="lg:col-span-2">
                <Button type="submit" disabled={isLoading} className="min-h-11 w-full gap-2 bg-[#163b39] text-white hover:bg-[#1d5954]">
                  {isLoading ? <Loader2 className="size-4 animate-spin" /> : <Globe2 className="size-4" />}
                  Scrape website
                </Button>
              </div>
            </form>
          </CardContent>
        </Card>

        <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader>
            <CardTitle className="text-lg">Pipeline notes</CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-[#48655d] sm:grid-cols-3 xl:grid-cols-1">
            <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
              <p className="font-semibold">Scrape</p>
              <p className="mt-1">Fetches live website content through Crawl4AI when available, with a fallback HTML parser for simpler pages.</p>
            </div>
            <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
              <p className="font-semibold">Analyze</p>
              <p className="mt-1">Parsed rows feed the review queue, suspicious-price scoring, and later normalization against canonical products.</p>
            </div>
            <div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
              <p className="font-semibold">Sort</p>
              <p className="mt-1">Once ingested, listings can be ranked by confidence, source trust, and price deviation before benchmark publication.</p>
            </div>
          </CardContent>
        </Card>
      </section>

      {error ? (
        <div className="page-enter rounded-2xl border border-[#f3c7bf] bg-[#fff0ec] px-4 py-3 text-sm text-[#a23a27]">{error}</div>
      ) : null}

      {result ? (
        <Card className="page-enter rounded-2xl border-[#dce8e3] bg-white shadow-none">
          <CardHeader className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
            <CardTitle className="flex items-center gap-2 text-lg"><Sparkles className="size-4 text-[#d9662b]" />Results</CardTitle>
            <div className="flex flex-wrap gap-2">
              <Badge variant="outline">{result.scraped} scraped</Badge>
              <Badge variant="outline">{result.ingested} ingested</Badge>
            </div>
          </CardHeader>
          <CardContent>
            <div className="grid gap-3 md:hidden">
              {result.listings.map((listing, index) => (
                <div key={`${listing.original_name}-card-${index}`} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                  <p className="font-medium text-[#173b39]">{listing.original_name}</p>
                  <div className="mt-3 grid grid-cols-2 gap-3 text-sm">
                    <div>
                      <p className="text-xs text-muted-foreground">Price</p>
                      <p className="font-semibold">{naira(listing.price)}</p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Seller</p>
                      <p className="truncate font-semibold">{listing.seller_name}</p>
                    </div>
                    <div className="col-span-2">
                      <p className="text-xs text-muted-foreground">Location</p>
                      <p>{listing.location || "Unspecified"}</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
            <div className="hidden overflow-x-auto rounded-xl border border-[#dce8e3] bg-white md:block">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Product</TableHead>
                    <TableHead>Price</TableHead>
                    <TableHead>Seller</TableHead>
                    <TableHead>Location</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {result.listings.map((listing, index) => (
                    <TableRow key={`${listing.original_name}-${index}`}>
                      <TableCell className="max-w-[360px] whitespace-normal font-medium xl:max-w-[520px]">{listing.original_name}</TableCell>
                      <TableCell>{naira(listing.price)}</TableCell>
                      <TableCell>{listing.seller_name}</TableCell>
                      <TableCell>{listing.location || "Unspecified"}</TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </div>
          </CardContent>
        </Card>
      ) : null}
    </WorkspaceShell>
  );
}

