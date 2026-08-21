"use client";

import { useEffect, useState } from "react";
import Image from "next/image";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
  LayoutDashboard,
  Package,
  Users,
  BarChart3,
  SearchCode,
  ListChecks,
  FileUp,
} from "lucide-react";
import { cn } from "@/lib/utils";
import { OpsOverview, fetchJson } from "@/lib/api";

export const navItems = [
  { title: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { title: "Products", href: "/products", icon: Package },
  { title: "Suppliers", href: "/suppliers", icon: Users },
  { title: "Analytics", href: "/analytics", icon: BarChart3 },
  { title: "Scrape", href: "/scrape", icon: SearchCode },
  { title: "Clean CSV", href: "/clean", icon: FileUp },
  { title: "Tasks", href: "/tasks", icon: ListChecks },
];

export function Sidebar() {
  const pathname = usePathname();
  const [ops, setOps] = useState<OpsOverview | null>(null);
  const [opsError, setOpsError] = useState(false);

  useEffect(() => {
    async function loadOps() {
      try {
        setOps(await fetchJson<OpsOverview>("/api/ops/overview"));
        setOpsError(false);
      } catch {
        setOps(null);
        setOpsError(true);
      }
    }

    loadOps();
  }, []);

  const openStages = ops?.tasks.filter((task) => task.stage !== "Completed").length;
  const reviewQueue = ops?.queue_metrics.find((metric) => metric.label === "Review queue")?.value;

  return (
    <aside className="sticky top-0 hidden h-screen w-64 shrink-0 border-r border-[#dce8e3] bg-[#f8fcf9] text-[#173b39] lg:flex lg:flex-col xl:w-72">
      <div className="border-b border-[#dce8e3] px-6 py-6">
        <div className="flex items-center gap-3">
          <Image
            src="/marketsense-mark.svg"
            alt="MarketSense logo"
            width={44}
            height={44}
            className="rounded-2xl"
          />
          <div>
            <h1 className="text-lg font-semibold tracking-tight">MarketSense</h1>
            <p className="text-xs text-[#6b8a80]">Price intelligence workspace</p>
          </div>
        </div>
        <div className="mt-5 rounded-2xl border border-[#dce8e3] bg-white px-4 py-3">
          <p className="text-[11px] uppercase tracking-[0.24em] text-[#6b8a80]">
            Workspace status
          </p>
          <p className="mt-2 text-sm text-[#48655d]">
            Ingest, clean, normalize, benchmark, and inspect market observations.
          </p>
        </div>
      </div>

      <nav className="flex-1 space-y-2 px-4 py-5">
        {navItems.map((item) => {
          const isActive = pathname === item.href;
          return (
            <Link
              key={item.href}
              href={item.href}
              className={cn(
                "flex items-center gap-3 rounded-xl px-4 py-3 text-sm font-medium transition-all",
                isActive
                  ? "bg-[#173b39] text-white shadow-[0_14px_34px_rgba(23,59,57,0.18)]"
                  : "text-[#48655d] hover:bg-white hover:text-[#173b39]"
              )}
            >
              <item.icon className="size-5" />
              {item.title}
            </Link>
          );
        })}
      </nav>

      <div className="border-t border-[#dce8e3] px-6 py-5">
        <div className="rounded-2xl border border-[#dce8e3] bg-white px-4 py-4 text-[#173b39]">
          <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#8a5f40]">
            Ops snapshot
          </p>
          {opsError ? (
            <p className="mt-2 text-sm font-medium text-[#a23a27]">Ops data unavailable</p>
          ) : ops ? (
            <>
              <p className="mt-2 text-sm font-medium">{openStages} open pipeline stages</p>
              <p className="text-sm text-[#48655d]">{reviewQueue ?? "0"} listings waiting for analyst review</p>
            </>
          ) : (
            <p className="mt-2 text-sm text-[#48655d]">Loading live state...</p>
          )}
        </div>
      </div>
    </aside>
  );
}
