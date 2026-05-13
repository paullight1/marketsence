export const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export type DashboardSummary = {
  total_products: number;
  total_suppliers: number;
  total_listings: number;
  suspicious_prices: number;
  avg_trust_score: number;
};

export type CategoryBreakdown = {
  category: string;
  count: number;
};

export type ProductSummary = {
  id: number;
  name: string;
  category: string | null;
  brand: string | null;
  avg_price: number;
  min_price: number;
  max_price: number;
  listings_count: number;
  last_updated: string | null;
};

export type SupplierSummary = {
  id: number;
  name: string;
  source: string;
  location: string | null;
  trust_score: number;
  total_listings: number;
  avg_price: number;
  suspicious_count: number;
};

export type OpsMetric = {
  label: string;
  value: string;
  tone: string;
};

export type OpsTask = {
  id: string;
  title: string;
  stage: string;
  owner: string;
  source: string;
  eta: string;
  progress: number;
  listings: number;
  note: string;
};

export type OpsReviewAlert = {
  id: string;
  product: string;
  issue: string;
  severity: string;
  delta: number;
};

export type OpsRecentListing = {
  id: number;
  product_name: string;
  price: number;
  seller: string;
  source: string;
  location: string | null;
  is_suspicious: boolean;
};

export type OpsOverview = {
  queue_metrics: OpsMetric[];
  tasks: OpsTask[];
  review_alerts: OpsReviewAlert[];
  recent_listings: OpsRecentListing[];
};

export async function fetchJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`);

  if (!response.ok) {
    throw new Error(`Request failed: ${response.status}`);
  }

  return response.json() as Promise<T>;
}
