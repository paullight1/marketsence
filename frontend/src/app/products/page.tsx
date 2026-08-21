"use client";

import { useEffect, useState } from "react";
import { ArrowDownWideNarrow } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { ProductSummary, fetchJson } from "@/lib/api";

function naira(value: number) {
  return new Intl.NumberFormat("en-NG", { style: "currency", currency: "NGN", maximumFractionDigits: 0 }).format(value);
}

export default function ProductsPage() {
  const [products, setProducts] = useState<ProductSummary[]>([]);
  const [search, setSearch] = useState("");
  const [category, setCategory] = useState("all");
  const [sortBy, setSortBy] = useState("listings");
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    async function loadProducts() {
      try {
        setProducts(await fetchJson<ProductSummary[]>("/api/products/?limit=100"));
      } catch (caught) {
        setProducts([]);
        setError(caught instanceof Error ? caught.message : "Could not load products");
      } finally {
        setIsLoading(false);
      }
    }
    loadProducts();
  }, []);

  const categories = Array.from(new Set(products.map((product) => product.category).filter(Boolean))) as string[];
  const filteredProducts = [...products].filter((product) => product.name.toLowerCase().includes(search.toLowerCase()) && (category === "all" || product.category === category)).sort((a, b) => sortBy === "price" ? b.avg_price - a.avg_price : b.listings_count - a.listings_count);

  return (
    <WorkspaceShell>
      <section className="page-enter flex flex-col gap-2"><span className="metric-pill w-fit">Catalog intelligence</span><h1 className="text-4xl font-semibold tracking-tight">Normalized products</h1><p className="max-w-3xl text-sm text-muted-foreground">Search and sort canonical products returned by the backend catalog.</p></section>

      {error ? <DataState error title="Product catalog unavailable" body={error} /> : isLoading ? <DataState title="Loading products" body="Reading the canonical catalog from the API." /> : (
        <>
          <section className="page-enter flex flex-wrap gap-4">
            <Input placeholder="Search products..." value={search} onChange={(event) => setSearch(event.target.value)} className="max-w-md bg-white" />
            <Select value={category} onValueChange={(value) => setCategory(value || "all")}><SelectTrigger className="max-w-[220px] bg-white"><SelectValue placeholder="Category" /></SelectTrigger><SelectContent><SelectItem value="all">All categories</SelectItem>{categories.map((cat) => <SelectItem key={cat} value={cat}>{cat}</SelectItem>)}</SelectContent></Select>
            <Select value={sortBy} onValueChange={(value) => setSortBy(value || "listings")}><SelectTrigger className="max-w-[220px] bg-white"><ArrowDownWideNarrow className="mr-2 size-4" /><SelectValue placeholder="Sort by" /></SelectTrigger><SelectContent><SelectItem value="listings">Sort by listings</SelectItem><SelectItem value="price">Sort by average price</SelectItem></SelectContent></Select>
          </section>
          <section className="page-enter grid gap-4 md:grid-cols-2 xl:grid-cols-3">
            {filteredProducts.map((product) => <Card key={product.id} className="rounded-2xl border-[#dce8e3] bg-white shadow-none"><CardHeader><CardTitle className="text-lg">{product.name}</CardTitle><p className="text-sm text-muted-foreground">{product.category || "Uncategorized"} - {product.brand || "No brand"}</p></CardHeader><CardContent className="space-y-4"><div><p className="text-3xl font-semibold">{naira(product.avg_price)}</p><p className="text-sm text-muted-foreground">Average observed price</p></div><div className="grid grid-cols-2 gap-3 text-sm"><div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-3"><p className="text-muted-foreground">Range</p><p className="mt-1 font-medium">{naira(product.min_price)} - {naira(product.max_price)}</p></div><div className="rounded-xl border border-[#dce8e3] bg-[#fbfefd] p-3"><p className="text-muted-foreground">Listings</p><p className="mt-1 font-medium">{product.listings_count}</p></div></div></CardContent></Card>)}
            {!filteredProducts.length ? <DataState title={products.length ? "No matching products" : "No products yet"} body={products.length ? "Adjust the search or category filter." : "Ingest listings and link them to canonical products before this catalog can populate."} /> : null}
          </section>
        </>
      )}
    </WorkspaceShell>
  );
}

function DataState({ title, body, error = false }: { title: string; body: string; error?: boolean }) {
  return <Card className={`rounded-2xl shadow-none ${error ? "border-red-200 bg-red-50" : "border-[#dce8e3] bg-white"}`}><CardContent className="p-6"><p className={`font-semibold ${error ? "text-red-800" : "text-[#173b39]"}`}>{title}</p><p className={`mt-1 text-sm ${error ? "text-red-700" : "text-muted-foreground"}`}>{body}</p></CardContent></Card>;
}
