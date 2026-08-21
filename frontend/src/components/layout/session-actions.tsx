"use client";

import Link from "next/link";
import { LogIn, LogOut } from "lucide-react";
import { useSyncExternalStore } from "react";
import { clearSession, getSession } from "@/lib/auth";

const subscribe = () => () => {};
const getClientSnapshot = () => Boolean(getSession());
const getServerSnapshot = () => false;

export function SessionActions() {
  const authenticated = useSyncExternalStore(
    subscribe,
    getClientSnapshot,
    getServerSnapshot,
  );

  if (!authenticated) {
    return <Link href="/login" className="inline-flex h-10 items-center gap-2 rounded-full border border-[#dce8e3] bg-white px-3 text-sm font-medium text-[#48655d] hover:text-[#173b39]"><LogIn className="size-4" />Sign in</Link>;
  }

  return <button type="button" onClick={() => { clearSession(); window.location.assign("/login"); }} className="inline-flex h-10 items-center gap-2 rounded-full border border-[#dce8e3] bg-white px-3 text-sm font-medium text-[#48655d] hover:text-[#173b39]"><LogOut className="size-4" />Sign out</button>;
}
