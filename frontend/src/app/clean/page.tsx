"use client";

import { FormEvent, useState } from "react";
import { CheckCircle2, Download, FileSpreadsheet, Loader2, Upload } from "lucide-react";
import { WorkspaceShell } from "@/components/layout/workspace-shell";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Input } from "@/components/ui/input";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

type CleanCsvResult = {
  file_id: string;
  download_filename: string;
  rows_before: number;
  rows_after: number;
  duplicates_removed: number;
  columns: string[];
  detected_name_column: string | null;
  detected_price_column: string | null;
  detected_date_column: string | null;
  missing_before: Record<string, number>;
  missing_after: Record<string, number>;
  preview: Record<string, string | number | boolean | null>[];
  message: string;
};

const apiBaseUrl = process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") || "http://localhost:8000";

export default function CleanCsvPage() {
  const [file, setFile] = useState<File | null>(null);
  const [result, setResult] = useState<CleanCsvResult | null>(null);
  const [error, setError] = useState("");
  const [isLoading, setIsLoading] = useState(false);

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!file) {
      setError("Choose a CSV file first.");
      return;
    }

    setError("");
    setResult(null);
    setIsLoading(true);

    const formData = new FormData();
    formData.append("file", file);

    try {
      const response = await fetch(`${apiBaseUrl}/api/ingest/clean-csv`, {
        method: "POST",
        body: formData,
      });
      const payload = await response.json();

      if (!response.ok) {
        throw new Error(payload.detail || "CSV cleaning failed");
      }

      setResult(payload);
    } catch (caught) {
      setError(caught instanceof Error ? caught.message : "CSV cleaning failed");
    } finally {
      setIsLoading(false);
    }
  }

  const previewColumns = result?.preview[0]
    ? Object.keys(result.preview[0]).slice(0, 8)
    : [];

  return (
    <WorkspaceShell>
      <section className="page-enter grid gap-6 xl:grid-cols-[0.95fr_1.05fr]">
        <Card className="glass-card rounded-[28px] shadow-none">
          <CardHeader>
            <div className="flex flex-wrap items-center gap-3">
              <span className="metric-pill">CSV cleaning</span>
              <span className="metric-pill">Human-review ready</span>
            </div>
            <CardTitle className="mt-3 text-3xl font-semibold tracking-tight">
              Upload a messy dataset and clean it into a usable file.
            </CardTitle>
          </CardHeader>
          <CardContent>
            <form onSubmit={handleSubmit} className="space-y-4">
              <label className="grid gap-2">
                <span className="text-sm font-medium">CSV file</span>
                <Input
                  type="file"
                  accept=".csv,text/csv"
                  className="bg-white/75"
                  onChange={(event) => setFile(event.target.files?.[0] || null)}
                />
              </label>

              <Button
                type="submit"
                disabled={isLoading}
                className="w-full gap-2 bg-[#163b39] text-white hover:bg-[#1d5954]"
              >
                {isLoading ? <Loader2 className="size-4 animate-spin" /> : <Upload className="size-4" />}
                Clean CSV
              </Button>
            </form>

            {error ? (
              <div className="mt-4 rounded-2xl border border-[#f3c7bf] bg-[#fff0ec] px-4 py-3 text-sm text-[#a23a27]">
                {error}
              </div>
            ) : null}
          </CardContent>
        </Card>

        <Card className="glass-card rounded-[28px] shadow-none">
          <CardHeader>
            <CardTitle className="flex items-center gap-2 text-lg">
              <FileSpreadsheet className="size-5 text-[#d9662b]" />
              Cleaning rules applied
            </CardTitle>
          </CardHeader>
          <CardContent className="grid gap-3 text-sm text-[#5c4b3f]">
            <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
              Normalizes column names and trims text values.
            </div>
            <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
              Detects product, price, and date columns when common names are present.
            </div>
            <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
              Adds `clean_name`, `clean_price`, and `clean_date` columns for downstream processing.
            </div>
            <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
              Fills missing `location` values and removes duplicate rows using stable listing fields.
            </div>
          </CardContent>
        </Card>
      </section>

      {result ? (
        <section className="page-enter grid gap-6">
          <Card className="glass-card rounded-[28px] shadow-none">
            <CardHeader className="flex flex-row items-center justify-between gap-4">
              <div>
                <CardTitle className="flex items-center gap-2 text-lg">
                  <CheckCircle2 className="size-5 text-[#166534]" />
                  Cleaned dataset summary
                </CardTitle>
                <p className="mt-1 text-sm text-muted-foreground">
                  {result.message}
                </p>
              </div>
              <a
                href={`${apiBaseUrl}/api/ingest/clean-csv/${result.file_id}/download`}
                className="inline-flex h-9 items-center justify-center gap-2 rounded-xl bg-[#163b39] px-3 text-sm font-medium text-white hover:bg-[#1d5954]"
              >
                <Download className="size-4" />
                Download CSV
              </a>
            </CardHeader>
            <CardContent className="grid gap-4 md:grid-cols-4">
              <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
                <p className="text-sm text-muted-foreground">Rows before</p>
                <p className="mt-2 text-3xl font-semibold">{result.rows_before.toLocaleString()}</p>
              </div>
              <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
                <p className="text-sm text-muted-foreground">Rows after</p>
                <p className="mt-2 text-3xl font-semibold">{result.rows_after.toLocaleString()}</p>
              </div>
              <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
                <p className="text-sm text-muted-foreground">Duplicates removed</p>
                <p className="mt-2 text-3xl font-semibold">{result.duplicates_removed.toLocaleString()}</p>
              </div>
              <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
                <p className="text-sm text-muted-foreground">Columns</p>
                <p className="mt-2 text-3xl font-semibold">{result.columns.length}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card rounded-[28px] shadow-none">
            <CardHeader>
              <CardTitle className="text-lg">Detected columns</CardTitle>
            </CardHeader>
            <CardContent className="grid gap-3 md:grid-cols-3">
              <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
                <p className="text-sm text-muted-foreground">Product name</p>
                <p className="mt-2 font-semibold">{result.detected_name_column || "Not detected"}</p>
              </div>
              <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
                <p className="text-sm text-muted-foreground">Price</p>
                <p className="mt-2 font-semibold">{result.detected_price_column || "Not detected"}</p>
              </div>
              <div className="rounded-2xl border border-[#eadfd1] bg-white/80 p-4">
                <p className="text-sm text-muted-foreground">Date</p>
                <p className="mt-2 font-semibold">{result.detected_date_column || "Not detected"}</p>
              </div>
            </CardContent>
          </Card>

          <Card className="glass-card rounded-[28px] shadow-none">
            <CardHeader>
              <CardTitle className="text-lg">Preview</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="overflow-x-auto rounded-2xl border border-[#eadfd1] bg-white/75">
                <Table>
                  <TableHeader>
                    <TableRow>
                      {previewColumns.map((column) => (
                        <TableHead key={column}>{column}</TableHead>
                      ))}
                    </TableRow>
                  </TableHeader>
                  <TableBody>
                    {result.preview.map((row, index) => (
                      <TableRow key={index}>
                        {previewColumns.map((column) => (
                          <TableCell key={column} className="max-w-[260px] truncate">
                            {row[column] === null || row[column] === undefined ? "Empty" : String(row[column])}
                          </TableCell>
                        ))}
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </div>
            </CardContent>
          </Card>
        </section>
      ) : null}
    </WorkspaceShell>
  );
}
