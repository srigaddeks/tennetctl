"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listProductLines, listProducts } from "@/lib/api";
import type { Product, ProductLine, ProductStatus } from "@/types/api";

type LinesState = { status: "loading" } | { status: "ok"; items: ProductLine[] } | { status: "error"; message: string };
type ProductsState = { status: "loading" } | { status: "ok"; items: Product[] } | { status: "error"; message: string };
type StatusFilter = ProductStatus | "all";

export default function ProductsListPage() {
  const [lines, setLines] = useState<LinesState>({ status: "loading" });
  const [products, setProducts] = useState<ProductsState>({ status: "loading" });
  const [productLineId, setProductLineId] = useState<string>("");
  const [status, setStatus] = useState<StatusFilter>("all");

  useEffect(() => {
    let cancelled = false;
    listProductLines()
      .then((items) => { if (!cancelled) setLines({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setLines({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, []);

  useEffect(() => {
    let cancelled = false;
    setProducts({ status: "loading" });
    listProducts({ product_line_id: productLineId || undefined, status: status === "all" ? undefined : status })
      .then((items) => { if (!cancelled) setProducts({ status: "ok", items }); })
      .catch((err: unknown) => { if (!cancelled) setProducts({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }); });
    return () => { cancelled = true; };
  }, [productLineId, status]);

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Products</h1>
        </div>
        <Link href="/catalog/products/new" className="btn-primary">+ New Product</Link>
      </div>

      <div className="filter-bar">
        <div className="filter-group">
          <span className="filter-label">Product Line</span>
          <select value={productLineId} onChange={(e) => setProductLineId(e.target.value)} className="erp-select" style={{ width: "auto", minWidth: 160 }}>
            <option value="">All product lines</option>
            {lines.status === "ok" && lines.items.map((l) => <option key={l.id} value={l.id}>{l.name} ({l.category_code})</option>)}
          </select>
        </div>
        <div className="filter-group">
          <span className="filter-label">Status</span>
          <select value={status} onChange={(e) => setStatus(e.target.value as StatusFilter)} className="erp-select" style={{ width: "auto", minWidth: 120 }}>
            <option value="all">All</option>
            <option value="active">Active</option>
            <option value="paused">Paused</option>
            <option value="discontinued">Discontinued</option>
          </select>
        </div>
      </div>

      <div className="rounded overflow-hidden" style={{ border: "1px solid var(--border)", backgroundColor: "var(--bg-card)" }}>
        {products.status === "loading" && <p className="p-6" style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading products…</p>}
        {products.status === "error" && (
          <div className="m-4 rounded p-4" style={{ border: "1px solid var(--status-error)", backgroundColor: "var(--status-error-bg)", color: "var(--status-error-text)", fontSize: 13 }}>
            <span style={{ fontWeight: 600 }}>Failed to load products</span>{" "}
            <span style={{ opacity: 0.8 }}>{products.message}</span>
          </div>
        )}
        {products.status === "ok" && products.items.length === 0 && (
          <div className="p-8 text-center" style={{ fontSize: 13, color: "var(--text-muted)" }}>No products match the current filters.</div>
        )}
        {products.status === "ok" && products.items.length > 0 && (
          <div className="overflow-x-auto">
            <table className="erp-table">
              <thead>
                <tr>
                  <th>Name</th>
                  <th>Product Line</th>
                  <th>Category</th>
                  <th>Serving (ml)</th>
                  <th>Price</th>
                  <th>Tags</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {products.items.map((p) => (
                  <tr key={p.id}>
                    <td style={{ fontWeight: 500 }}>{p.name}</td>
                    <td className="td-muted">{p.product_line_name}</td>
                    <td className="td-mono">{p.category_code}</td>
                    <td className="td-mono td-right">{p.default_serving_size_ml ?? "—"}</td>
                    <td className="td-mono td-right">
                      {p.default_selling_price !== null
                        ? `${parseFloat(String(p.default_selling_price)).toFixed(2)} ${p.currency_code}`
                        : "—"}
                    </td>
                    <td>
                      <div className="flex flex-wrap gap-1">
                        {p.tag_codes.length === 0
                          ? <span style={{ fontSize: 12, color: "var(--text-muted)" }}>—</span>
                          : p.tag_codes.map((tag) => (
                            <span key={tag} className="badge badge-draft">{tag}</span>
                          ))}
                      </div>
                    </td>
                    <td>
                      <span className={`badge badge-${p.status}`}>{p.status}</span>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
