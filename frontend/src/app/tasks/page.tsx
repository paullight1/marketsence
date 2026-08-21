"use client";

import { useCallback, useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, ListChecks, Loader2, Play } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { JobRecord, OpsOverview, fetchJson } from "@/lib/api";

const jobTone: Record<string, string> = { completed: "text-[#166534]", failed: "text-[#c2413a]", cancelled: "text-[#6b7280]", running: "text-[#2563eb]", retrying: "text-[#b45309]", queued: "text-[#173b39]" };

export default function TasksPage() {
  const [ops, setOps] = useState<OpsOverview | null>(null);
  const [jobs, setJobs] = useState<JobRecord[]>([]);
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(true);
  const [action, setAction] = useState("");

  const load = useCallback(async () => {
    setLoading(true); setError("");
    try {
      const [opsData, jobData] = await Promise.all([fetchJson<OpsOverview>("/api/ops/overview"), fetchJson<JobRecord[]>("/api/jobs/?limit=50")]);
      setOps(opsData); setJobs(jobData);
    } catch (caught) { setOps(null); setJobs([]); setError(caught instanceof Error ? caught.message : "Could not load job data"); }
    finally { setLoading(false); }
  }, []);

  useEffect(() => { void load(); }, [load]);

  async function queue(kind: "normalize" | "benchmark") {
    setAction(kind); setError("");
    try { await fetchJson<JobRecord>(`/api/jobs/${kind}`, { method: "POST", headers: { "Idempotency-Key": `${kind}-${new Date().toISOString().slice(0, 16)}` } }); await load(); }
    catch (caught) { setError(caught instanceof Error ? caught.message : `Could not queue ${kind}`); }
    finally { setAction(""); }
  }

  async function cancel(jobId: string) {
    setAction(jobId); try { await fetchJson<JobRecord>(`/api/jobs/${jobId}/cancel`, { method: "POST" }); await load(); } catch (caught) { setError(caught instanceof Error ? caught.message : "Could not cancel job"); } finally { setAction(""); }
  }

  return <WorkspaceShell>
    <section className="page-enter flex flex-wrap items-end justify-between gap-4"><div><span className="metric-pill">Durable worker queue</span><h1 className="mt-3 text-4xl font-semibold text-[#173b39]">Jobs and review workspace</h1><p className="mt-2 max-w-3xl text-sm text-[#48655d]">Long-running scrape, normalization, benchmark, and large-import operations are persisted before a worker executes them.</p></div><div className="flex gap-2"><Button variant="outline" onClick={() => queue("normalize")} disabled={Boolean(action)}>{action === "normalize" ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />} Normalize</Button><Button onClick={() => queue("benchmark")} disabled={Boolean(action)} className="bg-[#173b39] text-white">{action === "benchmark" ? <Loader2 className="size-4 animate-spin" /> : <Play className="size-4" />} Benchmark</Button></div></section>
    {error ? <p className="rounded-xl border border-red-200 bg-red-50 p-3 text-sm text-red-700">{error}</p> : null}
    {loading ? <State icon={<Clock3 className="size-5" />} title="Loading durable jobs" body="Reading job and pipeline state." /> : <>
      <section className="grid gap-4 md:grid-cols-4">{(ops?.queue_metrics ?? []).map((metric) => <Card key={metric.label} className="rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardContent className="p-5"><p className="text-sm text-muted-foreground">{metric.label}</p><p className="mt-2 text-3xl font-semibold text-[#173b39]">{metric.value}</p></CardContent></Card>)}</section>
      <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardHeader><CardTitle className="flex items-center gap-2"><ListChecks className="size-5" />Durable jobs</CardTitle></CardHeader><CardContent className="space-y-3">{jobs.map((job) => <div key={job.id} className="flex flex-wrap items-center justify-between gap-3 rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4"><div><p className="font-semibold capitalize">{job.job_type}</p><p className="text-xs text-muted-foreground">{job.id}</p><p className={`mt-1 text-sm font-medium ${jobTone[job.status] || ""}`}>{job.status} · attempt {job.attempts}/{job.max_attempts}</p>{job.error ? <p className="mt-1 max-w-2xl text-xs text-red-700">{job.error}</p> : null}</div>{["queued", "retrying", "running"].includes(job.status) ? <Button variant="outline" disabled={action === job.id} onClick={() => cancel(job.id)}>Cancel</Button> : null}</div>)}{!jobs.length ? <p className="rounded-xl border border-dashed p-4 text-sm text-muted-foreground">No durable jobs have been queued.</p> : null}</CardContent></Card>
      <section className="grid gap-6 lg:grid-cols-2"><State icon={<AlertTriangle className="size-5 text-[#b45309]" />} title="Retry and lease safety" body="Failed attempts back off; stale worker leases are recovered so abandoned work does not disappear." /><State icon={<CheckCircle2 className="size-5 text-[#166534]" />} title="Review remains separate" body="Durable execution does not auto-approve suspicious prices or unresolved catalog matches." /></section>
    </>}
  </WorkspaceShell>;
}

function State({ icon, title, body }: { icon: React.ReactNode; title: string; body: string }) { return <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardContent className="flex gap-3 p-6">{icon}<div><p className="font-semibold text-[#173b39]">{title}</p><p className="mt-1 text-sm text-[#48655d]">{body}</p></div></CardContent></Card>; }
