"use client";

import Link from "next/link";
import { FormEvent, useState } from "react";
import { Clock3, Globe2, Loader2 } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { JobRecord, fetchJson } from "@/lib/api";

export default function ScrapePage() {
  const [url, setUrl] = useState("");
  const [source, setSource] = useState("Website");
  const [sellerName, setSellerName] = useState("");
  const [location, setLocation] = useState("");
  const [maxItems, setMaxItems] = useState(25);
  const [ingest, setIngest] = useState(true);
  const [job, setJob] = useState<JobRecord | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault(); setError(""); setJob(null); setIsLoading(true);
    try {
      setJob(await fetchJson<JobRecord>("/api/jobs/scrape", {
        method: "POST",
        headers: { "Content-Type": "application/json", "Idempotency-Key": crypto.randomUUID() },
        body: JSON.stringify({ url, source, seller_name: sellerName || null, seller_source: "website", location: location || null, max_items: maxItems, ingest }),
      }));
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not queue scrape"); }
    finally { setIsLoading(false); }
  }

  return <WorkspaceShell>
    <section className="page-enter grid gap-6 xl:grid-cols-[1.1fr_0.9fr]">
      <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardHeader><div className="flex flex-wrap gap-2"><span className="metric-pill">Durable job</span><span className="metric-pill">Public-network targets only</span></div><CardTitle className="mt-3 text-3xl text-[#173b39]">Queue a website scrape</CardTitle></CardHeader><CardContent><form onSubmit={handleSubmit} className="grid gap-4 lg:grid-cols-2"><label className="grid gap-2 lg:col-span-2"><span className="text-sm font-medium">Website URL</span><Input required type="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com/products" /></label><label className="grid gap-2"><span className="text-sm font-medium">Source</span><Input required minLength={2} value={source} onChange={(e) => setSource(e.target.value)} /></label><label className="grid gap-2"><span className="text-sm font-medium">Seller override</span><Input value={sellerName} onChange={(e) => setSellerName(e.target.value)} /></label><label className="grid gap-2"><span className="text-sm font-medium">Location</span><Input value={location} onChange={(e) => setLocation(e.target.value)} /></label><label className="grid gap-2"><span className="text-sm font-medium">Max items</span><Input type="number" min={1} max={100} value={maxItems} onChange={(e) => setMaxItems(Math.min(100, Math.max(1, Number(e.target.value) || 1)))} /></label><label className="flex items-start gap-3 rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4 text-sm lg:col-span-2"><input type="checkbox" checked={ingest} onChange={(e) => setIngest(e.target.checked)} /><span>Persist successful extracted listings when the worker completes.</span></label><Button className="lg:col-span-2 gap-2 bg-[#173b39] text-white" disabled={isLoading}>{isLoading ? <Loader2 className="size-4 animate-spin" /> : <Globe2 className="size-4" />}{isLoading ? "Queueing..." : "Queue scrape"}</Button></form>{error ? <p className="mt-4 rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}</CardContent></Card>
      <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardHeader><CardTitle>Worker contract</CardTitle></CardHeader><CardContent className="space-y-3 text-sm text-[#48655d]"><p>Scrapes persist before execution, can retry after transient failures, and are lease-protected so abandoned work returns to the queue.</p><p>Idempotency prevents accidental duplicate queue records when callers retry the same request key.</p></CardContent></Card>
    </section>
    {job ? <Card className="page-enter rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardContent className="flex flex-wrap items-center justify-between gap-4 p-6"><div className="flex items-start gap-3"><Clock3 className="mt-1 size-5 text-[#3f8f78]" /><div><p className="font-semibold text-[#173b39]">Scrape queued</p><p className="text-sm text-muted-foreground">Job {job.id} · {job.status}</p></div></div><Link href="/tasks" className="rounded-xl bg-[#173b39] px-4 py-2 text-sm font-medium text-white">Open job queue</Link></CardContent></Card> : null}
  </WorkspaceShell>;
}
