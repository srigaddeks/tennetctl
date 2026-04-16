"use client";

import { useEffect, useRef, useState, useCallback } from "react";
import {
  Shield, Globe, Server, Database, Brain, Activity,
  FlaskConical, BookOpen, FileCheck, Lock, Bell, Search,
  Boxes, KeyRound, Zap, HardDrive, BarChart3, Layers,
  Download, Sun, Moon, ArrowLeft, Monitor, Bot, ShieldCheck,
  Users, Radio, Eye, ScrollText,
} from "lucide-react";
import { toPng } from "html-to-image";

/* ─── Service Box with tech detail ─── */
function Svc({ icon: I, label, tech, color, w = 128 }: {
  icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>;
  label: string; tech: string; color: string; w?: number;
}) {
  return (
    <div style={{
      width: w, padding: "12px 10px", borderRadius: 10, textAlign: "center",
      background: `color-mix(in srgb, ${color} 5%, var(--bg2))`,
      border: `1.5px solid color-mix(in srgb, ${color} 20%, transparent)`,
      display: "flex", flexDirection: "column", alignItems: "center", gap: 5,
      transition: "border-color 0.15s",
    }}>
      <div style={{
        width: 34, height: 34, borderRadius: 9,
        background: `linear-gradient(135deg, color-mix(in srgb, ${color} 15%, transparent), color-mix(in srgb, ${color} 5%, transparent))`,
        border: `1px solid color-mix(in srgb, ${color} 16%, transparent)`,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}><I size={17} color={color} strokeWidth={1.5} /></div>
      <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 10.5, color: "var(--white)", lineHeight: 1.2 }}>{label}</div>
      <div style={{ fontSize: 8, color: "var(--t4)", fontFamily: "'DM Mono', monospace", lineHeight: 1.3 }}>{tech}</div>
    </div>
  );
}

/* ─── Zone with accent bar ─── */
function Zone({ label, color, badge, children, isPrimary }: {
  label: string; color: string; badge?: string; children: React.ReactNode; isPrimary?: boolean;
}) {
  return (
    <div style={{
      border: `${isPrimary ? 2 : 1.5}px solid color-mix(in srgb, ${color} ${isPrimary ? 30 : 18}%, transparent)`,
      borderRadius: 12, background: `color-mix(in srgb, ${color} 2%, var(--bg))`,
      overflow: "hidden", flex: "1 1 0",
      boxShadow: isPrimary ? `0 0 20px color-mix(in srgb, ${color} 4%, transparent)` : "none",
    }}>
      <div style={{ height: isPrimary ? 2.5 : 1.5, background: `linear-gradient(90deg, transparent, color-mix(in srgb, ${color} ${isPrimary ? 50 : 35}%, transparent), transparent)` }} />
      <div style={{
        padding: "6px 12px", display: "flex", justifyContent: "space-between", alignItems: "center",
        borderBottom: `1px solid color-mix(in srgb, ${color} 8%, transparent)`,
      }}>
        <span style={{ fontSize: 8.5, fontFamily: "'Syne', sans-serif", fontWeight: 700, color: `color-mix(in srgb, ${color} 60%, var(--t3))`, textTransform: "uppercase", letterSpacing: 2 }}>{label}</span>
        {badge && <span style={{ fontSize: 7.5, fontFamily: "'DM Mono', monospace", color: "var(--t4)" }}>{badge}</span>}
      </div>
      <div style={{ padding: "10px 10px", display: "flex", gap: 7, justifyContent: "center", flexWrap: "wrap" }}>
        {children}
      </div>
    </div>
  );
}

/* ─── Connector ─── */
function Conn({ label, color, dir = "down" }: { label: string; color: string; dir?: "down" | "right" }) {
  const v = dir === "down";
  return (
    <div style={{ display: "flex", flexDirection: v ? "column" : "row", alignItems: "center", gap: 0, padding: v ? "3px 0" : "0 3px" }}>
      <div style={{ width: v ? 1.5 : 16, height: v ? 12 : 1.5, background: `color-mix(in srgb, ${color} 30%, transparent)`, borderRadius: 1 }} />
      <div style={{
        fontSize: 7.5, fontFamily: "'DM Mono', monospace", fontWeight: 600,
        color: `color-mix(in srgb, ${color} 55%, var(--t4))`,
        padding: "2px 8px", margin: v ? "2px 0" : "0 2px",
        border: `1px solid color-mix(in srgb, ${color} 14%, transparent)`,
        borderRadius: 4, background: "var(--bg)", whiteSpace: "nowrap",
      }}>{label}</div>
      <div style={{ width: v ? 1.5 : 16, height: v ? 12 : 1.5, background: `color-mix(in srgb, ${color} 30%, transparent)`, borderRadius: 1 }} />
      <div style={{ color: `color-mix(in srgb, ${color} 35%, transparent)`, fontSize: 10, fontWeight: 700, lineHeight: 1 }}>{v ? "↓" : "→"}</div>
    </div>
  );
}

export default function TechnicalOverviewPage() {
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
      const a = document.createElement("a"); a.href = url; a.download = "k-control-technical-overview.png"; a.click();
    });
  }, [isDark]);

  const blue = "#3b82f6", green = "#10b981", purple = "#a855f7", amber = "#f59e0b",
        indigo = "#6366f1", cyan = "#06b6d4", orange = "#f97316";

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", fontFamily: "'DM Sans', sans-serif" }}>
      {/* Nav */}
      <div style={{
        height: 52, background: "var(--bg2)", borderBottom: "1px solid var(--brd)",
        display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 24px",
        position: "sticky", top: 0, zIndex: 10,
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{ width: 30, height: 30, borderRadius: 7, background: "linear-gradient(135deg, #1d6ef5, #6366f1)", display: "flex", alignItems: "center", justifyContent: "center" }}>
            <Shield size={15} color="#fff" strokeWidth={2} />
          </div>
          <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 14, color: "var(--white)" }}>K-Control</span>
          <span style={{ fontSize: 11, color: "var(--t3)" }}>Technical Overview</span>
        </div>
        <div style={{ display: "flex", gap: 6 }}>
          <a href="/technical" style={{ padding: "5px 12px", borderRadius: 7, border: "1px solid var(--brd)", background: "var(--bg3)", color: "var(--t2)", fontSize: 11, textDecoration: "none", display: "flex", alignItems: "center", gap: 5 }}>
            <ArrowLeft size={11} /> Full View
          </a>
          <button onClick={exportPng} style={{ padding: "5px 12px", borderRadius: 7, border: "1px solid var(--brd)", background: "var(--bg3)", color: "var(--t2)", fontSize: 11, cursor: "pointer", display: "flex", alignItems: "center", gap: 5 }}>
            <Download size={11} /> Export 3x
          </button>
          <button onClick={toggleTheme} style={{ width: 34, height: 34, borderRadius: 7, border: "1px solid var(--brd)", background: "var(--bg3)", color: "var(--t2)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center" }}>
            {isDark ? <Sun size={14} /> : <Moon size={14} />}
          </button>
        </div>
      </div>

      {/* ═══ 16:9 SLIDE ═══ */}
      <div style={{ display: "flex", justifyContent: "center", padding: "32px 16px 48px" }}>
        <div
          ref={slideRef}
          style={{
            width: 1280, height: 720,
            background: "var(--bg)",
            border: "1px solid var(--brd)",
            borderRadius: 14,
            padding: "28px 36px 24px",
            position: "relative",
            overflow: "hidden",
            boxShadow: "0 8px 40px rgba(0,0,0,0.3)",
          }}
        >
          {/* BG glow */}
          <div style={{ position: "absolute", top: 0, left: 0, right: 0, bottom: 0, background: `radial-gradient(ellipse at 50% 10%, color-mix(in srgb, ${blue} 4%, transparent) 0%, transparent 50%)`, pointerEvents: "none" }} />

          <div style={{ position: "relative", height: "100%", display: "flex", flexDirection: "column" }}>

            {/* ── Header ── */}
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: 16 }}>
              <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                <div style={{ width: 34, height: 34, borderRadius: 9, background: "linear-gradient(135deg, #1d6ef5, #6366f1)", display: "flex", alignItems: "center", justifyContent: "center", boxShadow: "0 2px 8px rgba(29,110,245,0.25)" }}>
                  <Shield size={17} color="#fff" strokeWidth={2} />
                </div>
                <div>
                  <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 18, color: "var(--white)", letterSpacing: "-0.02em" }}>
                    K-Control — Technical Architecture
                  </div>
                  <div style={{ fontSize: 10, color: "var(--t3)" }}>Multi-Tenant Compliance & Governance Platform · AI-Powered · Deploy Anywhere</div>
                </div>
              </div>
              <div style={{ textAlign: "right" }}>
                <div style={{ fontSize: 9, color: "var(--t4)" }}>Kreesalis</div>
                <div style={{ fontSize: 8, color: "var(--t4)", fontFamily: "'DM Mono', monospace" }}>Cloud-Native · Kubernetes</div>
              </div>
            </div>

            {/* ── TIER 1: Presentation Layer ── */}
            <div style={{ display: "flex", gap: 10 }}>
              <Zone label="Clients" color={indigo}>
                <Svc icon={Globe} label="Web App" tech="SSR · React · PWA" color={indigo} w={105} />
                <Svc icon={Monitor} label="Mobile" tech="iOS · Android" color={indigo} w={90} />
                <Svc icon={Server} label="REST API" tech="SDKs · Webhooks" color={indigo} w={100} />
                <Svc icon={Radio} label="Events" tech="SSF/CAEP Streams" color={indigo} w={100} />
              </Zone>
              <Conn label="HTTPS · TLS" color={indigo} dir="right" />
              <Zone label="Edge & Security" color={blue} badge="Service Mesh · mTLS">
                <Svc icon={Lock} label="TLS Termination" tech="Certificate Mgmt" color={blue} w={110} />
                <Svc icon={ShieldCheck} label="mTLS Encryption" tech="Pod-to-Pod" color={blue} w={110} />
                <Svc icon={Activity} label="Load Balancer" tech="L7 · Weighted" color={blue} w={105} />
                <Svc icon={Shield} label="Rate Limiting" tech="Token Bucket" color={blue} w={100} />
              </Zone>
            </div>

            <Conn label="Internal Routing" color={blue} />

            {/* ── TIER 2: Application Layer ── */}
            <div style={{ display: "flex", gap: 8, alignItems: "stretch" }}>

              {/* Identity */}
              <Zone label="Identity & Governance" color={green}>
                <Svc icon={KeyRound} label="SSO · OAuth" tech="SAML · MFA · OIDC" color={green} w={100} />
                <Svc icon={Users} label="Multi-Tenant" tech="Orgs · Workspaces" color={green} w={100} />
                <Svc icon={ScrollText} label="Audit Trail" tech="Immutable · 7yr" color={green} w={100} />
              </Zone>

              <Conn label="JWT · RBAC" color={green} dir="right" />

              {/* Platform Core */}
              <Zone label="K-Control Platform" color={blue} badge="Kubernetes · HPA · Auto-Scaling" isPrimary>
                <Svc icon={Server} label="API Gateway" tech="Multi-Tenant · 61+ APIs" color={blue} />
                <Svc icon={Bell} label="Notifications" tech="Email · Push · SSF" color={cyan} w={115} />
                <Svc icon={FlaskConical} label="Sandbox" tech="Signals · Threats" color={green} w={110} />
                <Svc icon={BookOpen} label="GRC Library" tech="Frameworks · Tests" color={indigo} w={110} />
                <Svc icon={Brain} label="AI Copilot" tech="27 Modules · Codegen" color={purple} w={115} />
                <Svc icon={FileCheck} label="Risk Registry" tech="Assess · Mitigate" color={orange} w={110} />
                <Svc icon={Bot} label="AI Agents" tech="Autonomous · Tools" color={purple} w={110} />
              </Zone>

              <Conn label="LLM · RAG" color={purple} dir="right" />

              {/* AI */}
              <Zone label="AI & Intelligence" color={purple}>
                <Svc icon={Brain} label="AI Engine" tech="LLMs · Streaming" color={purple} w={100} />
                <Svc icon={Search} label="Knowledge" tech="Embeddings · RAG" color={purple} w={100} />
                <Svc icon={Eye} label="AI Monitoring" tech="Cost · Quality" color={purple} w={100} />
              </Zone>
            </div>

            <Conn label="Data Access" color={cyan} />

            {/* ── TIER 3: Data & Infrastructure ── */}
            <div style={{ display: "flex", gap: 8 }}>
              <Zone label="Data Layer" color={cyan} badge="Encrypted at Rest · Multi-Schema" isPrimary>
                <Svc icon={Database} label="Relational DB" tech="Primary · Encrypted" color={green} w={110} />
                <Svc icon={Zap} label="In-Memory Cache" tech="TTL · Invalidation" color={cyan} w={110} />
                <Svc icon={BarChart3} label="Analytics" tech="Time-Series · OLAP" color={amber} w={110} />
                <Svc icon={HardDrive} label="Object Storage" tech="S3 · GCS · Azure" color={blue} w={110} />
              </Zone>
              <Zone label="Observability" color={amber} badge="Full Telemetry Pipeline">
                <Svc icon={Activity} label="Telemetry" tech="Traces · Metrics · Logs" color={amber} w={115} />
                <Svc icon={Layers} label="Dashboards" tech="Real-Time · SLOs" color={amber} w={105} />
              </Zone>
              <Zone label="Asset Sources" color={orange}>
                <Svc icon={Boxes} label="Cloud" tech="Azure · AWS · GCP" color={orange} w={105} />
                <Svc icon={Server} label="On-Premises" tech="AD · Self-Hosted" color={orange} w={105} />
              </Zone>
            </div>

            {/* ── Bottom: Deploy + Security ── */}
            <div style={{ display: "flex", gap: 10, marginTop: "auto", paddingTop: 8 }}>
              <div style={{
                flex: 1, display: "flex", alignItems: "center", gap: 8,
                padding: "7px 14px", borderRadius: 9, border: "1px solid var(--brd)", background: "var(--bg2)",
              }}>
                <span style={{ fontSize: 8, fontFamily: "'Syne'", fontWeight: 700, color: "var(--t4)", textTransform: "uppercase", letterSpacing: 2, flexShrink: 0 }}>Deploy</span>
                {["Azure AKS", "Amazon EKS", "Google GKE", "On-Prem K8s", "Docker Compose"].map(d => (
                  <span key={d} style={{ fontSize: 8.5, color: "var(--t3)", padding: "2px 7px", borderRadius: 5, background: "var(--bg3)", border: "1px solid var(--brd)", whiteSpace: "nowrap" }}>{d}</span>
                ))}
                <span style={{ fontSize: 8, color: "var(--t4)", marginLeft: 4, fontFamily: "'DM Mono', monospace" }}>CI/CD · IaC · Rolling Updates</span>
              </div>
              <div style={{
                display: "flex", alignItems: "center", gap: 8,
                padding: "7px 14px", borderRadius: 9, border: `1px solid color-mix(in srgb, ${green} 12%, transparent)`, background: "var(--bg2)",
              }}>
                <Lock size={11} color={green} strokeWidth={1.8} />
                <span style={{ fontSize: 8.5, color: "var(--t3)" }}>AES-256 · JWT Rotation · RBAC · SSO · Audit · SSF/CAEP</span>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
