"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, CheckCircle2, Clock3, ListChecks, SearchCode } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OpsOverview, OpsTask, fetchJson } from "@/lib/api";

const columns = ["Blocked", "Queued", "Review", "Completed"] as const;

function tasksForStage(tasks: OpsTask[], stage: string) {
  return tasks.filter((task) => task.stage === stage);
}

export default function TasksPage() {
  const [ops, setOps] = useState<OpsOverview | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);
  const [reloadToken, setReloadToken] = useState(0);

  useEffect(() => {
    async function loadOps() {
      setIsLoading(true);
      setError("");
      try {
        setOps(await fetchJson<OpsOverview>("/api/ops/overview"));
      } catch (caught) {
        setOps(null);
        setError(caught instanceof Error ? caught.message : "Could not load task data");
      } finally {
        setIsLoading(false);
      }
    }

    loadOps();
  }, [reloadToken]);

  const tasks = ops?.tasks ?? [];

  return (
    <WorkspaceShell>
      <section className="page-enter flex flex-col gap-2">
        <span className="metric-pill w-fit">Persisted pipeline state</span>
        <h1 className="text-4xl font-semibold tracking-tight text-[#173b39]">Task and review workspace</h1>
        <p className="max-w-3xl text-sm text-[#48655d]">This board derives stage labels from persisted counts and benchmark history. It is not a background-job queue.</p>
      </section>

      {isLoading ? (
        <StateCard title="Loading pipeline state" body="Reading persisted pipeline and review counts." />
      ) : error || !ops ? (
        <StateCard title="Pipeline state unavailable" body={error || "No operations state was returned."} error action={<Button variant="outline" onClick={() => setReloadToken((value) => value + 1)}>Retry</Button>} />
      ) : (
        <>
          <section className="page-enter grid gap-4 md:grid-cols-4">
            {ops.queue_metrics.map((metric) => (
              <Card key={metric.label} className="rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardContent className="p-5"><p className="text-sm text-muted-foreground">{metric.label}</p><p className={`mt-2 text-3xl font-semibold ${metric.tone === "warning" ? "text-[#b45309]" : "text-[#173b39]"}`}>{metric.value}</p></CardContent></Card>
            ))}
          </section>

          <section className="page-enter grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
            <div className="grid gap-4 xl:grid-cols-4">
              {columns.map((column) => (
                <Card key={column} className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
                  <CardHeader><CardTitle className="text-base">{column}</CardTitle></CardHeader>
                  <CardContent className="space-y-3">
                    {tasksForStage(tasks, column).map((task) => (
                      <div key={task.id} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                        <p className="font-semibold">{task.title}</p><p className="mt-1 text-sm text-muted-foreground">{task.owner}</p><p className="mt-3 text-sm text-[#48655d]">{task.note}</p>
                        <div className="mt-4 h-2 rounded-full bg-[#e8f2ee]"><div className="h-2 rounded-full bg-[#3f8f78]" style={{ width: `${task.progress}%` }} /></div>
                        <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground"><span>{task.source}</span><span>{task.eta}</span></div>
                      </div>
                    ))}
                    {!tasksForStage(tasks, column).length ? <p className="rounded-xl border border-dashed border-[#dce8e3] bg-[#fbfefd] p-4 text-sm text-muted-foreground">No pipeline stage is in this state.</p> : null}
                  </CardContent>
                </Card>
              ))}
            </div>

            <div className="grid gap-6">
              <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
                <CardHeader><CardTitle className="text-base">Current execution contract</CardTitle></CardHeader>
                <CardContent className="space-y-4 text-sm text-[#48655d]">
                  <div className="flex items-start gap-3"><SearchCode className="mt-0.5 size-4 text-[#3f8f78]" /><span>Raw listing ingestion persists observations before normalization and benchmarking.</span></div>
                  <div className="flex items-start gap-3"><Clock3 className="mt-0.5 size-4 text-[#3f8f78]" /><span>Unresolved product matches remain visible instead of being counted as completed work.</span></div>
                  <div className="flex items-start gap-3"><AlertTriangle className="mt-0.5 size-4 text-[#b45309]" /><span>Benchmarking is blocked until listings are linked to canonical products.</span></div>
                  <div className="flex items-start gap-3"><CheckCircle2 className="mt-0.5 size-4 text-[#3f8f78]" /><span>Detected benchmark outliers create explicit analyst-review records.</span></div>
                </CardContent>
              </Card>

              <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
                <CardHeader className="flex flex-row items-center justify-between"><CardTitle className="text-base">Review feed</CardTitle><ListChecks className="size-4 text-muted-foreground" /></CardHeader>
                <CardContent className="space-y-3">
                  {ops.review_alerts.map((alert) => (
                    <div key={alert.id} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4"><p className="font-semibold">{alert.product}</p><p className="mt-1 text-sm text-muted-foreground">{alert.issue}</p><p className="mt-3 text-sm font-medium text-[#c2413a]">{alert.severity}</p></div>
                  ))}
                  {!ops.review_alerts.length ? <p className="rounded-xl border border-dashed border-[#dce8e3] bg-[#fbfefd] p-4 text-sm text-muted-foreground">No review records are waiting.</p> : null}
                </CardContent>
              </Card>
            </div>
          </section>
        </>
      )}
    </WorkspaceShell>
  );
}

function StateCard({ title, body, action, error = false }: { title: string; body: string; action?: React.ReactNode; error?: boolean }) {
  return <Card className={`page-enter rounded-2xl shadow-none ${error ? "border-red-200 bg-red-50" : "border-[#dce8e3] bg-white"}`}><CardContent className="flex flex-wrap items-center justify-between gap-4 p-6"><div><p className={`font-semibold ${error ? "text-red-800" : "text-[#173b39]"}`}>{title}</p><p className={`mt-1 text-sm ${error ? "text-red-700" : "text-[#48655d]"}`}>{body}</p></div>{action}</CardContent></Card>;
}
