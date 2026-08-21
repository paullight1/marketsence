"use client";

import { FormEvent, useState } from "react";
import { CheckCircle2, Download, FileSpreadsheet, Loader2, Upload } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { MAX_CSV_UPLOAD_BYTES, apiFetch, fetchJson } from "@/lib/api";

type CleanCsvResult = { file_id: string; download_filename: string; rows_before: number; rows_after: number; duplicates_removed: number; columns: string[]; detected_name_column: string | null; detected_price_column: string | null; detected_date_column: string | null; missing_before: Record<string, number>; missing_after: Record<string, number>; preview: Record<string, string | number | boolean | null>[]; message: string };
const maxCsvMb = MAX_CSV_UPLOAD_BYTES / (1024 * 1024);

export default function CleanCsvPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<CleanCsvResult | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);
  const [isDownloading, setIsDownloading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) { setError("Choose a CSV file first."); return; }
    if (file.size > MAX_CSV_UPLOAD_BYTES) { setError(`CSV file is too large. Maximum size is ${maxCsvMb} MB.`); return; }
    setError(""); setResult(null); setIsLoading(true);
    const formData = new FormData(); formData.append("file", file);
    try { setResult(await fetchJson<CleanCsvResult>("/api/ingest/clean-csv", { method: "POST", body: formData })); }
    catch (caught) { setError(caught instanceof Error ? caught.message : "CSV cleaning failed"); }
    finally { setIsLoading(false); }
  }

  async function downloadResult() {
    if (!result) return;
    setError(""); setIsDownloading(true);
    try {
      const response = await apiFetch(`/api/ingest/clean-csv/${result.file_id}/download`);
      if (!response.ok) throw new Error(`Download failed: ${response.status}`);
      const blob = await response.blob();
      const objectUrl = URL.createObjectURL(blob);
      const anchor = document.createElement("a");
      anchor.href = objectUrl; anchor.download = result.download_filename; anchor.click();
      URL.revokeObjectURL(objectUrl);
    } catch (caught) { setError(caught instanceof Error ? caught.message : "Download failed"); }
    finally { setIsDownloading(false); }
  }

  const previewColumns = result?.preview[0] ? Object.keys(result.preview[0]).slice(0, 8) : [];
  return (
    <WorkspaceShell>
      <section className="page-enter grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="glass-card rounded-[28px] shadow-none"><CardHeader><div className="flex flex-wrap items-center gap-3"><span className="metric-pill">CSV cleaning</span><span className="metric-pill">{maxCsvMb} MB limit</span></div><CardTitle className="mt-3 text-3xl font-semibold tracking-tight">Clean a messy market dataset into a safer export.</CardTitle></CardHeader><CardContent><form onSubmit={handleSubmit} className="space-y-4"><label className="grid gap-2"><span className="text-sm font-medium">CSV file</span><Input type="file" accept=".csv,text/csv" className="bg-white/75" onChange={(event) => { const selected = event.target.files?.[0] || null; setResult(null); if (selected && selected.size > MAX_CSV_UPLOAD_BYTES) { setFile(null); setError(`CSV file is too large. Maximum size is ${maxCsvMb} MB.`); } else { setFile(selected); setError(""); } }} /><span className="text-xs text-muted-foreground">The server enforces the same byte limit; oversized files are rejected before Pandas parsing.</span></label><Button type="submit" disabled={isLoading || !file} className="w-full gap-2 bg-[#163b39] text-white hover:bg-[#1d5954]">{isLoading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}{isLoading ? "Cleaning..." : "Clean CSV"}</Button></form>{error ? <div className="mt-4 rounded-2xl border border-[#f3c7bf] bg-[#fff0ec] px-4 py-3 text-sm text-[#a23a27]">{error}</div> : null}</CardContent></Card>
        <Card className="glass-card rounded-[28px] shadow-none"><CardHeader><CardTitle className="flex items-center gap-2 text-lg"><FileSpreadsheet className="size-5 text-[#d9662b]" />Cleaning rules applied</CardTitle></CardHeader><CardContent className="grid gap-3 text-sm text-[#5c4b3f]"><Rule>Normalizes and de-duplicates column names, then trims text values.</Rule><Rule>Detects common product, price, and date columns and adds normalized helper columns.</Rule><Rule>Fills missing location values and removes duplicate rows using stable listing fields.</Rule><Rule>Neutralizes spreadsheet-formula prefixes in the downloaded CSV to reduce formula-injection risk.</Rule></CardContent></Card>
      </section>
      {result ? <section className="page-enter grid gap-6"><Card className="glass-card rounded-[28px] shadow-none"><CardHeader className="flex flex-row items-center justify-between gap-4"><div><CardTitle className="flex items-center gap-2 text-lg"><CheckCircle2 className="size-5 text-[#166534]" />Cleaned dataset summary</CardTitle><p className="mt-1 text-sm text-muted-foreground">{result.message}</p></div><Button type="button" disabled={isDownloading} onClick={downloadResult} className="gap-2 bg-[#163b39] text-white hover:bg-[#1d5954]">{isDownloading ? <Loader2 className="size-4 animate-spin" /> : <Download className="size-4" />}{isDownloading ? "Downloading..." : "Download CSV"}</Button></CardHeader><CardContent className="grid gap-4 md:grid-cols-4"><Summary label="Rows before" value={result.rows_before.toLocaleString()} /><Summary label="Rows after" value={result.rows_after.toLocaleString()} /><Summary label="Duplicates removed" value={result.duplicates_removed.toLocaleString()} /><Summary label="Columns" value={String(result.columns.length)} /></CardContent></Card><Card className="glass-card rounded-[28px] shadow-none"><CardHeader><CardTitle className="text-lg">Detected columns</CardTitle></CardHeader><CardContent className="grid gap-3 md:grid-cols-3"><Detected label="Product name" value={result.detected_name_column || "Not detected"} /><Detected label="Price" value={result.detected_price_column || "Not detected"} /><Detected label="Date" value={result.detected_date_column || "Not detected"} /></CardContent></Card><Card className="glass-card rounded-[28px] shadow-none"><CardHeader><CardTitle className="text-lg">Preview</CardTitle></CardHeader><CardContent><div className="overflow-x-auto rounded-2xl border border-[#eadfd1] bg-white/75"><Table><TableHeader><TableRow>{previewColumns.map((column) => <TableHead key={column}>{column}</TableHead>)}</TableRow></TableHeader><TableBody>{result.preview.map((row, index) => <TableRow key={index}>{previewColumns.map((column) => <TableCell key={column} className="max-w-[260px] truncate">{row[column] === null || row[column] === undefined ? "Empty" : String(row[column])}</TableCell>)}</TableRow>)}</TableBody></Table></div></CardContent></Card></section> : null}
    </WorkspaceShell>
  );
}

function Rule({ children }: { children: React.ReactNode }) { return <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">{children}</div>; }
function Summary({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4"><p className="text-sm text-muted-foreground">{label}</p><p className="mt-2 text-3xl font-semibold">{value}</p></div>; }
function Detected({ label, value }: { label: string; value: string }) { return <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4"><p className="text-sm text-muted-foreground">{label}</p><p className="mt-2 font-semibold">{value}</p></div>; }
