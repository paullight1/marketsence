import { ReactNode } from "react";
import Link from "next/link";
import { Sidebar, navItems } from "@/components/layout/sidebar";
import { Bell, Search } from "lucide-react";

export function WorkspaceShell({
  children,
}: {
  children: ReactNode;
}) {
  return (
    <div className="flex min-h-screen bg-[linear-gradient(180deg,_#fffdf9,_#f7fbf9)]">
      <Sidebar />
      <main className="min-w-0 flex-1 overflow-y-auto">
        <header className="sticky top-0 z-20 border-b border-[#e5eee9] bg-white/88 backdrop-blur-md">
          <div className="mx-auto flex w-full max-w-7xl items-center justify-between gap-3 px-4 py-3 sm:px-5 md:px-8 md:py-4">
            <div className="min-w-0">
              <p className="text-xs font-semibold uppercase tracking-[0.22em] text-[#6b8a80]">
                MarketSense
              </p>
              <h2 className="truncate text-base font-semibold tracking-tight text-[#173b39] sm:text-lg">
                Price intelligence control room
              </h2>
            </div>
            <div className="hidden max-w-[320px] flex-1 items-center gap-2 rounded-full border border-[#dce8e3] bg-white px-4 py-2 text-sm text-muted-foreground xl:flex">
              <Search className="size-4" />
              <span className="truncate">Search products, suppliers, or jobs</span>
            </div>
            <button className="grid size-10 shrink-0 place-items-center rounded-full border border-[#dce8e3] bg-white text-[#173b39]">
              <Bell className="size-4" />
            </button>
          </div>
          <nav className="mx-auto flex w-full max-w-7xl gap-2 overflow-x-auto px-4 pb-3 sm:px-5 lg:hidden">
            {navItems.map((item) => (
              <Link
                key={item.href}
                href={item.href}
                className="shrink-0 rounded-full border border-[#dce8e3] bg-[#f8fcf9] px-3 py-2 text-xs font-medium text-[#48655d]"
              >
                {item.title}
              </Link>
            ))}
          </nav>
        </header>
        <div className="mx-auto flex w-full max-w-7xl flex-col gap-5 px-4 py-5 sm:px-5 md:px-8 md:py-8">
          {children}
        </div>
      </main>
    </div>
  );
}
