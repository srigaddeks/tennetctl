"use client";

import Link from "next/link";
import { useEffect, useState } from "react";
import { listPipelineStages, listDeals, updateDeal } from "@/lib/api";
import type { PipelineStage, Deal, DealStatus } from "@/types/api";

type StagesState =
  | { status: "loading" }
  | { status: "ok"; stages: PipelineStage[] }
  | { status: "error"; message: string };

type DealsState =
  | { status: "loading" }
  | { status: "ok"; deals: Deal[] }
  | { status: "error"; message: string };

const DEAL_STATUS_STYLES: Record<DealStatus, string> = {
  open: "bg-blue-100 text-blue-800",
  won: "bg-green-100 text-green-800",
  lost: "bg-red-100 text-red-800",
};

export default function PipelinePage() {
  const [stagesState, setStagesState] = useState<StagesState>({ status: "loading" });
  const [dealsState, setDealsState] = useState<DealsState>({ status: "loading" });

  function reload() {
    listDeals({ status: "open" })
      .then((deals) => setDealsState({ status: "ok", deals }))
      .catch((err: unknown) => setDealsState({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }

  useEffect(() => {
    listPipelineStages()
      .then((stages) => setStagesState({ status: "ok", stages }))
      .catch((err: unknown) => setStagesState({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
    listDeals({ status: "open" })
      .then((deals) => setDealsState({ status: "ok", deals }))
      .catch((err: unknown) => setDealsState({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }, []);

  async function handleMoveDeal(dealId: string, stageId: string) {
    try {
      await updateDeal(dealId, { stage_id: stageId });
      reload();
    } catch {
      // silently fail — table will stay stale, user can reload
    }
  }

  if (stagesState.status === "loading") return <div style={{ padding: 32, color: "var(--text-muted)" }}>Loading pipeline…</div>;
  if (stagesState.status === "error") return <div style={{ padding: 32, color: "var(--status-error)" }}>{stagesState.message}</div>;

  if (stagesState.stages.length === 0) {
    return (
      <div className="max-w-5xl">
        <div className="page-header">
          <div>
            <h1 className="page-title">Pipeline</h1>
            <p className="page-subtitle">Deals organized by stage</p>
          </div>
        </div>
        <div className="rounded border p-12 text-center" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <p style={{ fontSize: 16, fontWeight: 600, color: "var(--text-primary)", marginBottom: 8 }}>No pipeline stages configured</p>
          <p style={{ fontSize: 13, color: "var(--text-muted)", marginBottom: 16 }}>Create pipeline stages to start organizing your deals.</p>
          <Link href="/deals" className="btn-primary">Go to Deals →</Link>
        </div>
      </div>
    );
  }

  const stages = [...stagesState.stages].sort((a, b) => a.order_position - b.order_position);
  const deals = dealsState.status === "ok" ? dealsState.deals : [];

  const dealsByStage = stages.reduce<Record<string, Deal[]>>((acc, stage) => {
    acc[stage.id] = deals.filter(d => d.stage_id === stage.id);
    return acc;
  }, {});

  const unstagedDeals = deals.filter(d => !d.stage_id);

  return (
    <div>
      <div className="page-header">
        <div>
          <h1 className="page-title">Pipeline</h1>
          <p className="page-subtitle">{deals.length} open deal{deals.length !== 1 ? "s" : ""} across {stages.length} stage{stages.length !== 1 ? "s" : ""}</p>
        </div>
        <Link href="/deals" className="btn-secondary">List View</Link>
      </div>

      <div style={{ display: "flex", gap: 12, overflowX: "auto", paddingBottom: 16 }}>
        {stages.map((stage) => {
          const stageDeals = dealsByStage[stage.id] ?? [];
          const totalValue = stageDeals.reduce((s, d) => s + (d.value ?? 0), 0);

          return (
            <div key={stage.id} style={{ minWidth: 260, maxWidth: 280, flex: "0 0 260px" }}>
              {/* Column header */}
              <div style={{
                padding: "10px 14px",
                borderRadius: "8px 8px 0 0",
                backgroundColor: stage.color ? `${stage.color}18` : "#F1F5F9",
                borderLeft: `3px solid ${stage.color || "#94A3B8"}`,
                borderTop: "1px solid var(--border)",
                borderRight: "1px solid var(--border)",
              }}>
                <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-primary)" }}>{stage.name}</div>
                <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>
                  {stageDeals.length} deal{stageDeals.length !== 1 ? "s" : ""} · {totalValue > 0 ? `₹${totalValue.toLocaleString()}` : "₹0"}
                </div>
              </div>

              {/* Cards */}
              <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border)", borderTop: "none", borderRadius: "0 0 8px 8px", minHeight: 200, padding: 8, display: "flex", flexDirection: "column", gap: 8 }}>
                {stageDeals.map((deal) => (
                  <DealCard key={deal.id} deal={deal} stages={stages} onMove={handleMoveDeal} />
                ))}
                {stageDeals.length === 0 && (
                  <div style={{ textAlign: "center", padding: "24px 0", fontSize: 12, color: "var(--text-muted)" }}>
                    No deals
                  </div>
                )}
              </div>
            </div>
          );
        })}

        {/* Unstaged column */}
        {unstagedDeals.length > 0 && (
          <div style={{ minWidth: 260, maxWidth: 280, flex: "0 0 260px" }}>
            <div style={{ padding: "10px 14px", borderRadius: "8px 8px 0 0", backgroundColor: "#F1F5F9", border: "1px solid var(--border)" }}>
              <div style={{ fontSize: 12, fontWeight: 700, color: "var(--text-secondary)" }}>Unstaged</div>
              <div style={{ fontSize: 11, color: "var(--text-muted)", marginTop: 2 }}>{unstagedDeals.length} deal{unstagedDeals.length !== 1 ? "s" : ""}</div>
            </div>
            <div style={{ backgroundColor: "var(--bg-surface)", border: "1px solid var(--border)", borderTop: "none", borderRadius: "0 0 8px 8px", minHeight: 200, padding: 8, display: "flex", flexDirection: "column", gap: 8 }}>
              {unstagedDeals.map((deal) => (
                <DealCard key={deal.id} deal={deal} stages={stages} onMove={handleMoveDeal} />
              ))}
            </div>
          </div>
        )}
      </div>

      {dealsState.status === "error" && (
        <p style={{ color: "var(--status-error)", fontSize: 13, marginTop: 12 }}>Failed to load deals: {dealsState.message}</p>
      )}
    </div>
  );
}

function DealCard({ deal, stages, onMove }: {
  deal: Deal;
  stages: PipelineStage[];
  onMove: (dealId: string, stageId: string) => void;
}) {
  const [showMove, setShowMove] = useState(false);

  return (
    <div style={{ backgroundColor: "#fff", border: "1px solid var(--border)", borderRadius: 6, padding: "10px 12px" }}>
      <div style={{ fontSize: 13, fontWeight: 600, color: "var(--text-primary)", marginBottom: 4 }}>{deal.title}</div>
      {deal.contact_name && (
        <div style={{ fontSize: 11, color: "var(--text-muted)", marginBottom: 4 }}>{deal.contact_name}</div>
      )}
      <div style={{ display: "flex", gap: 6, alignItems: "center", flexWrap: "wrap", marginBottom: 6 }}>
        {deal.value !== null && (
          <span style={{ fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--text-primary)", fontWeight: 600 }}>
            {deal.currency === "INR" ? "₹" : deal.currency + " "}{Number(deal.value).toLocaleString()}
          </span>
        )}
        {deal.expected_close_date && (
          <span style={{ fontSize: 11, color: "var(--text-muted)" }}>
            Close: {new Date(deal.expected_close_date).toLocaleDateString()}
          </span>
        )}
        <span className={`inline-flex items-center rounded px-1.5 py-0.5 text-xs font-medium ${DEAL_STATUS_STYLES[deal.status]}`}>
          {deal.status}
        </span>
      </div>

      <button
        onClick={() => setShowMove(!showMove)}
        style={{ fontSize: 11, color: "var(--accent)", background: "none", border: "none", cursor: "pointer", padding: 0, textDecoration: "underline" }}
      >
        Move to stage
      </button>

      {showMove && (
        <select
          style={{ display: "block", marginTop: 6, width: "100%", padding: "4px 6px", fontSize: 12, border: "1px solid var(--border)", borderRadius: 4 }}
          defaultValue={deal.stage_id ?? ""}
          onChange={e => { onMove(deal.id, e.target.value); setShowMove(false); }}
        >
          <option value="" disabled>Select stage…</option>
          {stages.map(s => (
            <option key={s.id} value={s.id}>{s.name}</option>
          ))}
        </select>
      )}
    </div>
  );
}
