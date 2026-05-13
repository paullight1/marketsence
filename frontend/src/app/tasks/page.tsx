"use client";

import { useEffect, useState } from "react";
import { CheckCircle2, Clock3, ListChecks, RotateCcw, SearchCode } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { OpsOverview, OpsTask, fetchJson } from "@/lib/api";

const columns = ["Queued", "Running", "Review", "Completed"] as const;

function tasksForStage(tasks: OpsTask[], stage: string) {
  return tasks.filter((task) => task.stage === stage);
}

export default function TasksPage() {
  const [ops, setOps] = useState<OpsOverview | null>(null);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadOps() {
      try {
        setOps(await fetchJson<OpsOverview>("/api/ops/overview"));
      } catch (caught) {
        setError(caught instanceof Error ? caught.message : "Could not load task data");
      }
    }

    loadOps();
  }, []);

  const tasks = ops?.tasks ?? [];

  return (
    <WorkspaceShell>
      <section className="page-enter flex flex-col gap-2">
        <span className="metric-pill w-fit">System design surface</span>
        <h1 className="text-4xl font-semibold tracking-tight text-[#173b39]">
          Task and queue workspace
        </h1>
        <p className="max-w-3xl text-sm text-[#48655d]">
          This board is generated from live database counts: scrape intake, matching backlog, human review, and benchmark output.
        </p>
        {error ? (
          <p className="w-fit rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">
            {error}
          </p>
        ) : null}
      </section>

      <section className="page-enter grid gap-4 md:grid-cols-4">
        {(ops?.queue_metrics ?? []).map((metric) => (
          <Card key={metric.label} className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
            <CardContent className="p-5">
              <p className="text-sm text-muted-foreground">{metric.label}</p>
              <p className={`mt-2 text-3xl font-semibold ${metric.tone === "warning" ? "text-[#b45309]" : "text-[#173b39]"}`}>
                {metric.value}
              </p>
            </CardContent>
          </Card>
        ))}
      </section>

      <section className="page-enter grid gap-6 xl:grid-cols-[1.2fr_0.8fr]">
        <div className="grid gap-4 xl:grid-cols-4">
          {columns.map((column) => (
            <Card key={column} className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
              <CardHeader>
                <CardTitle className="text-base">{column}</CardTitle>
              </CardHeader>
              <CardContent className="space-y-3">
                {tasksForStage(tasks, column).map((task) => (
                  <div key={task.id} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                    <p className="font-semibold">{task.title}</p>
                    <p className="mt-1 text-sm text-muted-foreground">{task.owner}</p>
                    <p className="mt-3 text-sm text-[#48655d]">{task.note}</p>
                    <div className="mt-4 h-2 rounded-full bg-[#e8f2ee]">
                      <div className="h-2 rounded-full bg-[#3f8f78]" style={{ width: `${task.progress}%` }} />
                    </div>
                    <div className="mt-4 flex items-center justify-between text-xs text-muted-foreground">
                      <span>{task.source}</span>
                      <span>{task.eta}</span>
                    </div>
                  </div>
                ))}
                {!tasksForStage(tasks, column).length ? (
                  <p className="rounded-xl border border-dashed border-[#dce8e3] bg-[#fbfefd] p-4 text-sm text-muted-foreground">
                    No active jobs.
                  </p>
                ) : null}
              </CardContent>
            </Card>
          ))}
        </div>

        <div className="grid gap-6">
          <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
            <CardHeader>
              <CardTitle className="text-base">Execution checklist</CardTitle>
            </CardHeader>
            <CardContent className="space-y-4 text-sm text-[#48655d]">
              <div className="flex items-start gap-3"><SearchCode className="mt-0.5 size-4 text-[#3f8f78]" /><span>Scrape jobs are isolated from processing and can be retried safely.</span></div>
              <div className="flex items-start gap-3"><RotateCcw className="mt-0.5 size-4 text-[#3f8f78]" /><span>Failed fetches stay visible as backlog instead of disappearing silently.</span></div>
              <div className="flex items-start gap-3"><Clock3 className="mt-0.5 size-4 text-[#3f8f78]" /><span>Human review remains explicit for risky matches and abnormal prices.</span></div>
              <div className="flex items-start gap-3"><CheckCircle2 className="mt-0.5 size-4 text-[#3f8f78]" /><span>Completed jobs publish into analytics only after verification.</span></div>
            </CardContent>
          </Card>

          <Card className="rounded-2xl border-[#dce8e3] bg-white shadow-none">
            <CardHeader className="flex flex-row items-center justify-between">
              <CardTitle className="text-base">High-risk reviews</CardTitle>
              <ListChecks className="size-4 text-muted-foreground" />
            </CardHeader>
            <CardContent className="space-y-3">
              {(ops?.review_alerts ?? []).map((alert) => (
                <div key={alert.id} className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-4">
                  <p className="font-semibold">{alert.product}</p>
                  <p className="mt-1 text-sm text-muted-foreground">{alert.issue}</p>
                  <p className="mt-3 text-sm font-medium text-[#c2413a]">
                    {alert.delta}% delta - {alert.severity}
                  </p>
                </div>
              ))}
              {ops && !ops.review_alerts.length ? (
                <p className="rounded-xl border border-dashed border-[#dce8e3] bg-[#fbfefd] p-4 text-sm text-muted-foreground">
                  No high-risk reviews are waiting.
                </p>
              ) : null}
            </CardContent>
          </Card>
        </div>
      </section>
    </WorkspaceShell>
  );
}
