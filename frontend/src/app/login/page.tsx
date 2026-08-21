"use client";

import { FormEvent, useState } from "react";
import { Loader2, LockKeyhole } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { API_BASE_URL } from "@/lib/api";
import { saveSession } from "@/lib/auth";

type LoginResponse = {
  access_token: string;
  token_type: string;
  role: string;
  expires_in: number;
};

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  async function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setError("");
    setLoading(true);
    try {
      const response = await fetch(`${API_BASE_URL}/api/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      const payload = (await response.json()) as LoginResponse & { detail?: string };
      if (!response.ok) throw new Error(payload.detail || `Sign in failed: ${response.status}`);
      saveSession(payload.access_token, payload.role, payload.expires_in);
      window.location.assign("/dashboard");
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "Sign in failed");
    } finally {
      setLoading(false);
    }
  }

  return (
    <main className="grid min-h-screen place-items-center bg-[linear-gradient(180deg,_#fffdf9,_#f7fbf9)] px-4 py-10">
      <Card className="w-full max-w-md rounded-[28px] border-[#dce8e3] bg-white shadow-none">
        <CardHeader>
          <div className="mb-2 grid size-11 place-items-center rounded-2xl bg-[#173b39] text-white"><LockKeyhole className="size-5" /></div>
          <CardTitle className="text-2xl text-[#173b39]">Sign in to MarketSense</CardTitle>
          <p className="text-sm text-muted-foreground">Access tokens stay in this browser tab session and are sent only through the Authorization header.</p>
        </CardHeader>
        <CardContent>
          <form onSubmit={submit} className="space-y-4">
            <label className="grid gap-2"><span className="text-sm font-medium">Username</span><Input required autoComplete="username" value={username} onChange={(event) => setUsername(event.target.value)} /></label>
            <label className="grid gap-2"><span className="text-sm font-medium">Password</span><Input required type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} /></label>
            {error ? <p className="rounded-xl border border-red-200 bg-red-50 px-3 py-2 text-sm text-red-700">{error}</p> : null}
            <Button type="submit" disabled={loading} className="w-full gap-2 bg-[#173b39] text-white hover:bg-[#1d5954]">{loading ? <Loader2 className="size-4 animate-spin" /> : null}{loading ? "Signing in..." : "Sign in"}</Button>
          </form>
        </CardContent>
      </Card>
    </main>
  );
}
