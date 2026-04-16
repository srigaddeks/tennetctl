"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  Shield, Globe, Server, Database, Brain, Activity,
  FlaskConical, BookOpen, FileCheck, Lock,
  Bell, Search, Boxes, Monitor, KeyRound, Zap, HardDrive,
  BarChart3, Layers, Download, Sun, Moon, ArrowLeft,
} from "lucide-react";
import { toPng } from "html-to-image";

/* ─── Slide-optimized components ─── */

function Pill({ icon: Icon, label, color }: {
  icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>;
  label: string; color: string;
}) {
  return (
    <div style={{
      display: "inline-flex", alignItems: "center", gap: 8,
      padding: "8px 16px", borderRadius: 10,
      background: `color-mix(in srgb, ${color} 6%, var(--bg2))`,
      border: `1.5px solid color-mix(in srgb, ${color} 18%, transparent)`,
    }}>
      <div style={{
        width: 28, height: 28, borderRadius: 7,
        background: `color-mix(in srgb, ${color} 12%, transparent)`,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}><Icon size={14} color={color} strokeWidth={1.6} /></div>
      <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 12, color: "var(--white)" }}>{label}</span>
    </div>
  );
}

function FlowArrow({ color }: { color: string }) {
  return (
    <div style={{ display: "flex", alignItems: "center", margin: "0 4px" }}>
      <div style={{ width: 28, height: 2, background: `color-mix(in srgb, ${color} 30%, transparent)`, borderRadius: 1 }} />
      <div style={{ color: `color-mix(in srgb, ${color} 40%, transparent)`, fontSize: 14, fontWeight: 700, marginLeft: -2 }}>→</div>
    </div>
  );
}

function FlowArrowDown({ color }: { color: string }) {
  return (
    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", margin: "4px 0" }}>
      <div style={{ width: 2, height: 20, background: `color-mix(in srgb, ${color} 30%, transparent)`, borderRadius: 1 }} />
      <div style={{ color: `color-mix(in srgb, ${color} 40%, transparent)`, fontSize: 14, fontWeight: 700, marginTop: -4 }}>↓</div>
    </div>
  );
}

function TierLabel({ label, color }: { label: string; color: string }) {
  return (
    <div style={{
      fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 10,
      color: `color-mix(in srgb, ${color} 60%, var(--t3))`,
      textTransform: "uppercase", letterSpacing: 3,
      marginBottom: 12, paddingBottom: 6,
      borderBottom: `1px solid color-mix(in srgb, ${color} 12%, transparent)`,
      display: "flex", alignItems: "center", gap: 8,
    }}>
      <div style={{ width: 16, height: 2, background: color, borderRadius: 1 }} />
      {label}
    </div>
  );
}

function LargeBox({ icon: Icon, label, sub, color, w = 140 }: {
  icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>;
  label: string; sub: string; color: string; w?: number;
}) {
  return (
    <div style={{
      width: w, padding: "16px 12px", borderRadius: 12,
      background: `color-mix(in srgb, ${color} 4%, var(--bg2))`,
      border: `1.5px solid color-mix(in srgb, ${color} 18%, transparent)`,
      display: "flex", flexDirection: "column", alignItems: "center", gap: 8,
      textAlign: "center",
    }}>
      <div style={{
        width: 44, height: 44, borderRadius: 12,
        background: `linear-gradient(135deg, color-mix(in srgb, ${color} 14%, transparent), color-mix(in srgb, ${color} 5%, transparent))`,
        border: `1px solid color-mix(in srgb, ${color} 16%, transparent)`,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}><Icon size={22} color={color} strokeWidth={1.5} /></div>
      <div>
        <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 13, color: "var(--white)", lineHeight: 1.2 }}>{label}</div>
        <div style={{ fontSize: 10, color: "var(--t3)", marginTop: 3, lineHeight: 1.4 }}>{sub}</div>
      </div>
    </div>
  );
}

export default function SlidePage() {
  const [isDark, setIsDark] = useState(true);
  const slideRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    const saved = localStorage.getItem("kc-arch-theme");
    if (saved === "light") { setIsDark(false); document.documentElement.classList.add("light"); }
  }, []);

  const toggleTheme = useCallback(() => {
    setIsDark(prev => {
      const next = !prev;
      document.documentElement.classList.toggle("light", next);
      localStorage.setItem("kc-arch-theme", next ? "light" : "dark");
      return next;
    });
  }, []);

  const exportPng = useCallback(() => {
    if (!slideRef.current) return;
    toPng(slideRef.current, { backgroundColor: isDark ? "#060b16" : "#f8fafc", pixelRatio: 3 }).then(url => {
      const a = document.createElement("a"); a.href = url; a.download = "k-control-slide-architecture.png"; a.click();
    });
  }, [isDark]);

  const blue = "#3b82f6", green = "#10b981", purple = "#a855f7", amber = "#f59e0b",
        indigo = "#6366f1", cyan = "#06b6d4", orange = "#f97316";

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", fontFamily: "'DM Sans', sans-serif" }}>
      {/* Nav */}
      <div style={{
        height: 56, background: "var(--bg2)", borderBottom: "1px solid var(--brd)",
        display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 28px",
        position: "sticky", top: 0, zIndex: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: "linear-gradient(135deg, #1d6ef5, #6366f1)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}><Shield size={17} color="#fff" strokeWidth={2} /></div>
          <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 15, color: "var(--white)" }}>K-Control</span>
          <div style={{ width: 1, height: 22, background: "var(--brd)", margin: "0 8px" }} />
          <span style={{ fontSize: 12, color: "var(--t2)", fontWeight: 500 }}>Slide View</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <a href="/technical" style={{
            padding: "7px 16px", borderRadius: 8, border: "1px solid var(--brd)", background: "var(--bg3)",
            color: "var(--t2)", fontSize: 12, textDecoration: "none", display: "flex", alignItems: "center", gap: 6, fontWeight: 500,
          }}><ArrowLeft size={13} /> Full View</a>
          <button onClick={exportPng} style={{
            padding: "7px 16px", borderRadius: 8, border: "1px solid var(--brd)", background: "var(--bg3)",
            color: "var(--t2)", fontSize: 12, cursor: "pointer", display: "flex", alignItems: "center", gap: 6, fontWeight: 500,
          }}><Download size={13} /> Export 3x PNG</button>
          <button onClick={toggleTheme} style={{
            width: 38, height: 38, borderRadius: 8, border: "1px solid var(--brd)", background: "var(--bg3)",
            color: "var(--t2)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
          }}>{isDark ? <Sun size={15} /> : <Moon size={15} />}</button>
        </div>
      </div>

      {/* ═══ SLIDE CANVAS — 16:9 aspect ratio ═══ */}
      <div style={{ display: "flex", justifyContent: "center", padding: "40px 20px 60px" }}>
        <div
          ref={slideRef}
          style={{
            width: 1280, height: 720,
            background: "var(--bg)",
            border: "1px solid var(--brd)",
            borderRadius: 16,
            padding: "36px 48px",
            position: "relative",
            overflow: "hidden",
            boxShadow: "0 8px 40px rgba(0,0,0,0.3)",
          }}
        >
          {/* Subtle gradient bg */}
          <div style={{
            position: "absolute", top: 0, left: 0, right: 0, bottom: 0,
            background: `radial-gradient(ellipse at 50% 20%, color-mix(in srgb, ${blue} 4%, transparent) 0%, transparent 60%)`,
            pointerEvents: "none",
          }} />

          <div style={{ position: "relative", height: "100%", display: "flex", flexDirection: "column" }}>

            {/* Header */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 28 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
                <div style={{
                  width: 38, height: 38, borderRadius: 10,
                  background: "linear-gradient(135deg, #1d6ef5, #6366f1)",
                  display: "flex", alignItems: "center", justifyContent: "center",
                  boxShadow: "0 2px 10px rgba(29,110,245,0.3)",
                }}><Shield size={19} color="#fff" strokeWidth={2} /></div>
                <div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 22, color: "var(--white)", letterSpacing: "-0.02em" }}>
                    K-Control Platform Architecture
                  </div>
                  <div style={{ fontSize: 11, color: "var(--t3)", marginTop: 1 }}>
                    Enterprise Compliance & Governance &middot; AI-Powered &middot; Deploy Anywhere
                  </div>
                </div>
              </div>
              <div style={{ fontSize: 10, color: "var(--t4)" }}>by Kreesalis</div>
            </div>

            {/* Main content */}
            <div style={{ flex: 1, display: "flex", flexDirection: "column", gap: 12 }}>

              {/* TIER 1: Presentation */}
              <TierLabel label="Presentation Tier" color={indigo} />
              <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 4 }}>
                <Pill icon={Globe} label="Web App" color={indigo} />
                <Pill icon={Monitor} label="Mobile" color={indigo} />
                <Pill icon={Server} label="REST API" color={indigo} />
                <FlowArrow color={indigo} />
                <Pill icon={Lock} label="Service Mesh" color={blue} />
                <Pill icon={Shield} label="mTLS" color={blue} />
                <Pill icon={Activity} label="Load Balancer" color={blue} />
              </div>

              <FlowArrowDown color={blue} />

              {/* TIER 2: Application */}
              <TierLabel label="Application Tier" color={blue} />
              <div style={{ display: "flex", gap: 14 }}>
                {/* Core */}
                <div style={{
                  flex: "0 0 auto", padding: "14px 18px", borderRadius: 14,
                  border: `2px solid color-mix(in srgb, ${blue} 25%, transparent)`,
                  background: `color-mix(in srgb, ${blue} 2%, var(--bg))`,
                }}>
                  <div style={{ fontSize: 9, fontFamily: "'Syne'", fontWeight: 700, color: "var(--t4)", textTransform: "uppercase", letterSpacing: 2, marginBottom: 10 }}>Core</div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <LargeBox icon={KeyRound} label="Identity" sub="SSO · RBAC · MFA" color={green} w={120} />
                    <LargeBox icon={Server} label="API Gateway" sub="Multi-Tenant · 61+" color={blue} w={120} />
                    <LargeBox icon={Bell} label="Notifications" sub="Email · Push · SSF" color={cyan} w={120} />
                  </div>
                </div>

                {/* Domain */}
                <div style={{
                  flex: 1, padding: "14px 18px", borderRadius: 14,
                  border: `2px solid color-mix(in srgb, ${green} 25%, transparent)`,
                  background: `color-mix(in srgb, ${green} 2%, var(--bg))`,
                }}>
                  <div style={{ fontSize: 9, fontFamily: "'Syne'", fontWeight: 700, color: "var(--t4)", textTransform: "uppercase", letterSpacing: 2, marginBottom: 10 }}>Domain Modules</div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <LargeBox icon={FlaskConical} label="Sandbox" sub="Signals · Policies" color={green} w={110} />
                    <LargeBox icon={BookOpen} label="GRC Library" sub="Frameworks · Tests" color={indigo} w={110} />
                    <LargeBox icon={Brain} label="AI Copilot" sub="27 Modules" color={purple} w={110} />
                    <LargeBox icon={FileCheck} label="Risk Registry" sub="Assess · Mitigate" color={orange} w={110} />
                  </div>
                </div>

                {/* AI */}
                <div style={{
                  flex: "0 0 auto", padding: "14px 18px", borderRadius: 14,
                  border: `2px solid color-mix(in srgb, ${purple} 25%, transparent)`,
                  background: `color-mix(in srgb, ${purple} 2%, var(--bg))`,
                }}>
                  <div style={{ fontSize: 9, fontFamily: "'Syne'", fontWeight: 700, color: "var(--t4)", textTransform: "uppercase", letterSpacing: 2, marginBottom: 10 }}>Intelligence</div>
                  <div style={{ display: "flex", gap: 10 }}>
                    <LargeBox icon={Brain} label="AI Engine" sub="LLMs · Streaming" color={purple} w={110} />
                    <LargeBox icon={Search} label="Knowledge" sub="Embeddings · RAG" color={purple} w={110} />
                  </div>
                </div>
              </div>

              <FlowArrowDown color={cyan} />

              {/* TIER 3: Data + Infrastructure */}
              <div style={{ display: "flex", gap: 14 }}>
                {/* Data */}
                <div style={{ flex: 1 }}>
                  <TierLabel label="Data Tier" color={cyan} />
                  <div style={{ display: "flex", gap: 10 }}>
                    <LargeBox icon={Database} label="Database" sub="Encrypted · Multi-Schema" color={green} w={130} />
                    <LargeBox icon={Zap} label="Cache" sub="In-Memory · Fast" color={cyan} w={110} />
                    <LargeBox icon={BarChart3} label="Analytics" sub="Time-Series · OLAP" color={amber} w={110} />
                    <LargeBox icon={HardDrive} label="Storage" sub="Multi-Provider" color={blue} w={110} />
                    <LargeBox icon={Boxes} label="Assets" sub="Cloud · On-Prem" color={orange} w={110} />
                  </div>
                </div>
                {/* Observability */}
                <div style={{ flex: "0 0 auto" }}>
                  <TierLabel label="Observability" color={amber} />
                  <div style={{ display: "flex", gap: 10 }}>
                    <LargeBox icon={Activity} label="Telemetry" sub="Traces · Metrics" color={amber} w={110} />
                    <LargeBox icon={Layers} label="Dashboards" sub="Real-Time Alerts" color={amber} w={110} />
                  </div>
                </div>
              </div>

              {/* Bottom bar: Deploy targets + Security */}
              <div style={{ display: "flex", gap: 14, marginTop: "auto" }}>
                <div style={{
                  flex: 1, display: "flex", alignItems: "center", gap: 12,
                  padding: "8px 16px", borderRadius: 10,
                  border: "1px solid var(--brd)", background: "var(--bg2)",
                }}>
                  <span style={{ fontSize: 9, fontFamily: "'Syne'", fontWeight: 700, color: "var(--t4)", textTransform: "uppercase", letterSpacing: 2 }}>Deploy</span>
                  {["Azure AKS", "Amazon EKS", "Google GKE", "On-Premises K8s", "Docker Compose"].map(d => (
                    <span key={d} style={{ fontSize: 10, color: "var(--t3)", padding: "3px 10px", borderRadius: 6, background: "var(--bg3)", border: "1px solid var(--brd)" }}>{d}</span>
                  ))}
                </div>
                <div style={{
                  display: "flex", alignItems: "center", gap: 10,
                  padding: "8px 16px", borderRadius: 10,
                  border: `1px solid color-mix(in srgb, ${green} 15%, transparent)`, background: "var(--bg2)",
                }}>
                  <Lock size={13} color={green} strokeWidth={1.6} />
                  <span style={{ fontSize: 10, color: "var(--t3)" }}>Encrypted &middot; RBAC &middot; SSO &middot; Audit Trail &middot; SSF/CAEP</span>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
