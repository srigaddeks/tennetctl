"use client";

import { useEffect, useState } from "react";
import {
  getPipelineSummary,
  getLeadConversion,
  getActivitySummary,
  getContactGrowth,
} from "@/lib/api";
import type {
  PipelineSummaryStage,
  LeadConversionRow,
  ActivitySummaryRow,
  ContactGrowthPoint,
} from "@/types/api";

type State<T> =
  | { status: "loading" }
  | { status: "ok"; data: T }
  | { status: "error"; message: string };

function HBar({ label, value, max, color }: { label: string; value: number; max: number; color?: string }) {
  const pct = max > 0 ? Math.round((value / max) * 100) : 0;
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 8 }}>
      <div style={{ minWidth: 120, fontSize: 12, color: "var(--text-secondary)", textAlign: "right", overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap" }}>{label}</div>
      <div style={{ flex: 1, height: 20, backgroundColor: "#F1F5F9", borderRadius: 4, overflow: "hidden" }}>
        <div style={{ width: `${pct}%`, height: "100%", backgroundColor: color ?? "var(--accent)", borderRadius: 4, minWidth: pct > 0 ? 4 : 0 }} />
      </div>
      <div style={{ minWidth: 40, fontSize: 12, fontFamily: "var(--font-mono)", color: "var(--text-primary)", textAlign: "right" }}>{value}</div>
    </div>
  );
}

export default function ReportsPage() {
  const [pipeline, setPipeline] = useState<State<PipelineSummaryStage[]>>({ status: "loading" });
  const [leadConv, setLeadConv] = useState<State<LeadConversionRow[]>>({ status: "loading" });
  const [actSummary, setActSummary] = useState<State<ActivitySummaryRow[]>>({ status: "loading" });
  const [contactGrowth, setContactGrowth] = useState<State<ContactGrowthPoint[]>>({ status: "loading" });

  useEffect(() => {
    getPipelineSummary()
      .then((data) => setPipeline({ status: "ok", data }))
      .catch((err: unknown) => setPipeline({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));

    getLeadConversion()
      .then((data) => setLeadConv({ status: "ok", data }))
      .catch((err: unknown) => setLeadConv({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));

    getActivitySummary()
      .then((data) => setActSummary({ status: "ok", data }))
      .catch((err: unknown) => setActSummary({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));

    getContactGrowth()
      .then((data) => setContactGrowth({ status: "ok", data }))
      .catch((err: unknown) => setContactGrowth({ status: "error", message: err instanceof Error ? err.message : "Unknown error" }));
  }, []);

  // Pipeline max values
  const pipelineMaxValue = pipeline.status === "ok"
    ? Math.max(...pipeline.data.map(s => s.total_value), 1)
    : 1;
  const pipelineMaxDeals = pipeline.status === "ok"
    ? Math.max(...pipeline.data.map(s => s.deal_count), 1)
    : 1;

  // Lead conversion max
  const leadMax = leadConv.status === "ok"
    ? Math.max(...leadConv.data.map(r => r.lead_count), 1)
    : 1;

  // Activity summary: group by type
  const actByType = actSummary.status === "ok"
    ? actSummary.data.reduce<Record<string, number>>((acc, row) => {
        acc[row.activity_type] = (acc[row.activity_type] ?? 0) + row.count;
        return acc;
      }, {})
    : {};
  const actMax = Math.max(...Object.values(actByType), 1);

  // Contact growth
  const growthMax = contactGrowth.status === "ok"
    ? Math.max(...contactGrowth.data.map(p => p.new_contacts), 1)
    : 1;

  return (
    <div className="max-w-5xl">
      <div className="page-header">
        <div>
          <h1 className="page-title">Reports</h1>
          <p className="page-subtitle">Pipeline summary, lead conversion, activity metrics, and growth</p>
        </div>
      </div>

      <div className="grid grid-cols-1 gap-6 lg:grid-cols-2">

        {/* 1. Pipeline Summary */}
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>Pipeline Summary</h2>

          {pipeline.status === "loading" && <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading…</p>}
          {pipeline.status === "error" && <p style={{ fontSize: 13, color: "var(--status-error)" }}>Failed to load pipeline data.</p>}
          {pipeline.status === "ok" && pipeline.data.length === 0 && (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No pipeline data available.</p>
          )}
          {pipeline.status === "ok" && pipeline.data.length > 0 && (
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 8 }}>Deal Value by Stage</div>
              {pipeline.data.map((stage) => (
                <HBar
                  key={stage.stage_id ?? "unstaged"}
                  label={stage.stage_name ?? "Unstaged"}
                  value={stage.total_value}
                  max={pipelineMaxValue}
                  color={stage.stage_color ?? "var(--accent)"}
                />
              ))}
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 8, marginTop: 16 }}>Deal Count by Stage</div>
              {pipeline.data.map((stage) => (
                <HBar
                  key={`count-${stage.stage_id ?? "unstaged"}`}
                  label={stage.stage_name ?? "Unstaged"}
                  value={stage.deal_count}
                  max={pipelineMaxDeals}
                  color={stage.stage_color ?? "#94A3B8"}
                />
              ))}
            </div>
          )}
        </div>

        {/* 2. Lead Conversion */}
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>Lead Conversion</h2>

          {leadConv.status === "loading" && <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading…</p>}
          {leadConv.status === "error" && <p style={{ fontSize: 13, color: "var(--status-error)" }}>Failed to load lead data.</p>}
          {leadConv.status === "ok" && leadConv.data.length === 0 && (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No lead data available.</p>
          )}
          {leadConv.status === "ok" && leadConv.data.length > 0 && (
            <div>
              {leadConv.data.map((row) => {
                const colorMap: Record<string, string> = {
                  new: "var(--grey-700)",
                  contacted: "#F59E0B",
                  qualified: "#10B981",
                  unqualified: "#EF4444",
                  converted: "#8B5CF6",
                };
                return (
                  <HBar
                    key={row.status}
                    label={row.status.charAt(0).toUpperCase() + row.status.slice(1)}
                    value={row.lead_count}
                    max={leadMax}
                    color={colorMap[row.status] ?? "var(--accent)"}
                  />
                );
              })}
            </div>
          )}
        </div>

        {/* 3. Activity Summary */}
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>Activity Summary</h2>

          {actSummary.status === "loading" && <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading…</p>}
          {actSummary.status === "error" && <p style={{ fontSize: 13, color: "var(--status-error)" }}>Failed to load activity data.</p>}
          {actSummary.status === "ok" && Object.keys(actByType).length === 0 && (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No activity data available.</p>
          )}
          {actSummary.status === "ok" && Object.keys(actByType).length > 0 && (
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 8 }}>Total by Type</div>
              {Object.entries(actByType).map(([type, count]) => {
                const colorMap: Record<string, string> = {
                  task: "#6366F1",
                  call: "#10B981",
                  email: "var(--grey-700)",
                  meeting: "#F59E0B",
                  note: "#94A3B8",
                };
                return (
                  <HBar
                    key={type}
                    label={type.charAt(0).toUpperCase() + type.slice(1)}
                    value={count}
                    max={actMax}
                    color={colorMap[type] ?? "var(--accent)"}
                  />
                );
              })}

              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 8, marginTop: 16 }}>Breakdown</div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "4px 8px", color: "var(--text-muted)", fontWeight: 600, fontSize: 11 }}>Type</th>
                      <th style={{ textAlign: "left", padding: "4px 8px", color: "var(--text-muted)", fontWeight: 600, fontSize: 11 }}>Status</th>
                      <th style={{ textAlign: "right", padding: "4px 8px", color: "var(--text-muted)", fontWeight: 600, fontSize: 11 }}>Count</th>
                    </tr>
                  </thead>
                  <tbody>
                    {actSummary.data.map((row, i) => (
                      <tr key={i}>
                        <td style={{ padding: "3px 8px", color: "var(--text-secondary)", textTransform: "capitalize" }}>{row.activity_type}</td>
                        <td style={{ padding: "3px 8px", color: "var(--text-secondary)", textTransform: "capitalize" }}>{row.status}</td>
                        <td style={{ padding: "3px 8px", color: "var(--text-primary)", textAlign: "right", fontFamily: "var(--font-mono)" }}>{row.count}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>

        {/* 4. Contact Growth */}
        <div className="rounded border p-5" style={{ backgroundColor: "var(--bg-card)", borderColor: "var(--border)" }}>
          <h2 style={{ fontSize: 13, fontWeight: 700, marginBottom: 16, color: "var(--text-primary)" }}>Contact Growth</h2>

          {contactGrowth.status === "loading" && <p style={{ fontSize: 13, color: "var(--text-muted)" }}>Loading…</p>}
          {contactGrowth.status === "error" && <p style={{ fontSize: 13, color: "var(--status-error)" }}>Failed to load growth data.</p>}
          {contactGrowth.status === "ok" && contactGrowth.data.length === 0 && (
            <p style={{ fontSize: 13, color: "var(--text-muted)" }}>No growth data available.</p>
          )}
          {contactGrowth.status === "ok" && contactGrowth.data.length > 0 && (
            <div>
              <div style={{ fontSize: 10.5, fontWeight: 700, textTransform: "uppercase", letterSpacing: "0.06em", color: "var(--text-muted)", marginBottom: 8 }}>Contacts Created per Week</div>
              <div style={{ display: "flex", alignItems: "flex-end", gap: 4, height: 80, marginBottom: 12 }}>
                {contactGrowth.data.map((point) => {
                  const h = growthMax > 0 ? Math.round((point.new_contacts / growthMax) * 64) : 0;
                  return (
                    <div
                      key={point.week}
                      title={`${point.week}: ${point.new_contacts} contacts`}
                      style={{
                        flex: 1,
                        height: Math.max(h, 2),
                        backgroundColor: "var(--accent)",
                        borderRadius: "2px 2px 0 0",
                        opacity: 0.8,
                        cursor: "default",
                      }}
                    />
                  );
                })}
              </div>
              <div style={{ overflowX: "auto" }}>
                <table style={{ width: "100%", fontSize: 12, borderCollapse: "collapse" }}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: "left", padding: "4px 8px", color: "var(--text-muted)", fontWeight: 600, fontSize: 11 }}>Week</th>
                      <th style={{ textAlign: "right", padding: "4px 8px", color: "var(--text-muted)", fontWeight: 600, fontSize: 11 }}>New Contacts</th>
                    </tr>
                  </thead>
                  <tbody>
                    {contactGrowth.data.map((point) => (
                      <tr key={point.week}>
                        <td style={{ padding: "3px 8px", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", fontSize: 11 }}>{point.week}</td>
                        <td style={{ padding: "3px 8px", color: "var(--text-primary)", textAlign: "right", fontFamily: "var(--font-mono)" }}>{point.new_contacts}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
