import { clearSession, getAccessToken } from "@/lib/auth";

export const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";
export const MAX_CSV_UPLOAD_BYTES = 5 * 1024 * 1024;

export type DashboardSummary = { total_products: number; total_suppliers: number; total_listings: number; suspicious_prices: number; avg_trust_score: number };
export type CategoryBreakdown = { category: string; count: number };
export type ProductSummary = { id: number; name: string; category: string | null; brand: string | null; avg_price: number; min_price: number; max_price: number; listings_count: number; last_updated: string | null };
export type SupplierSummary = { id: number; name: string; source: string; location: string | null; trust_score: number; total_listings: number; avg_price: number; suspicious_count: number };
export type OpsMetric = { label: string; value: string; tone: string };
export type OpsTask = { id: string; title: string; stage: string; owner: string; source: string; eta: string; progress: number; listings: number; note: string };
export type OpsReviewAlert = { id: string; product: string; issue: string; severity: string; delta: number };
export type OpsRecentListing = { id: number; product_name: string; price: number; seller: string; source: string; location: string | null; is_suspicious: boolean };
export type OpsOverview = { queue_metrics: OpsMetric[]; tasks: OpsTask[]; review_alerts: OpsReviewAlert[]; recent_listings: OpsRecentListing[] };
export type JobRecord = { id: string; job_type: string; status: string; payload: Record<string, unknown>; result: Record<string, unknown> | null; error: string | null; attempts: number; max_attempts: number; created_at: string; updated_at: string; started_at: string | null; completed_at: string | null; cancel_requested: boolean };

type ApiErrorBody = { detail?: unknown };

export async function apiFetch(path: string, init?: RequestInit): Promise<Response> {
  const headers = new Headers(init?.headers);
  const token = getAccessToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);
  const response = await fetch(`${API_BASE_URL}${path}`, { ...init, headers });
  if (response.status === 401 && typeof window !== "undefined" && window.location.pathname !== "/login") {
    clearSession();
    window.location.assign("/login");
  }
  return response;
}

export async function fetchJson<T>(path: string, init?: RequestInit): Promise<T> {
  const response = await apiFetch(path, init);
  if (!response.ok) {
    let detail = `Request failed: ${response.status}`;
    try {
      const payload = (await response.json()) as ApiErrorBody;
      if (typeof payload.detail === "string") detail = payload.detail;
      else if (Array.isArray(payload.detail)) {
        const messages = payload.detail.map((item) => item && typeof item === "object" && "msg" in item ? String((item as { msg: unknown }).msg) : "").filter(Boolean);
        if (messages.length) detail = messages.join("; ");
      }
    } catch {}
    throw new Error(detail);
  }
  return response.json() as Promise<T>;
}
