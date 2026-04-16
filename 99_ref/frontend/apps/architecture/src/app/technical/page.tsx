"use client";

import { useCallback, useEffect, useState, useRef } from "react";
import {
  Shield, Globe, Smartphone, Code2, Server, Database, Brain, Zap,
  BarChart3, HardDrive, Cloud, Activity, Eye, Search, Lock, Bell,
  FlaskConical, BookOpen, Users, KeyRound, Radio,
  LayoutDashboard, ShieldCheck, ScrollText, Monitor, RadioTower,
  Sun, Moon, ArrowLeft, Boxes, AlertTriangle, Bot, Container,
  Layers, FileCheck, Workflow, Download, ChevronRight, Gauge,
  ArrowUpDown, Network, Cpu,
} from "lucide-react";
import { toPng } from "html-to-image";

/* ═══════════════════════════════════════════════════════
   COMPONENTS
   ═══════════════════════════════════════════════════════ */

function TechBox({ icon: Icon, label, sub, color, size = "md" }: {
  icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>;
  label: string; sub?: string; color: string; size?: "sm" | "md" | "lg";
}) {
  const w = size === "lg" ? 190 : size === "sm" ? 120 : 148;
  const iconSz = size === "lg" ? 22 : size === "sm" ? 15 : 18;
  const fs = size === "lg" ? 12 : size === "sm" ? 10.5 : 11;
  return (
    <div style={{
      width: w, background: `color-mix(in srgb, ${color} 4%, var(--bg2))`,
      border: `1.5px solid color-mix(in srgb, ${color} 18%, transparent)`,
      borderRadius: 10, padding: size === "sm" ? "10px 10px" : "14px 14px",
      display: "flex", flexDirection: "column", alignItems: "center", gap: size === "sm" ? 6 : 8,
      transition: "all 0.2s ease", cursor: "default",
    }}
    onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.borderColor = `color-mix(in srgb, ${color} 45%, transparent)`; e.currentTarget.style.boxShadow = `0 8px 24px color-mix(in srgb, ${color} 12%, transparent)`; }}
    onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.borderColor = `color-mix(in srgb, ${color} 18%, transparent)`; e.currentTarget.style.boxShadow = "none"; }}
    >
      <div style={{
        width: iconSz + 18, height: iconSz + 18, borderRadius: 10,
        background: `linear-gradient(135deg, color-mix(in srgb, ${color} 12%, transparent), color-mix(in srgb, ${color} 5%, transparent))`,
        border: `1px solid color-mix(in srgb, ${color} 14%, transparent)`,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}>
        <Icon size={iconSz} color={color} strokeWidth={1.5} />
      </div>
      <div style={{ textAlign: "center" }}>
        <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: fs, color: "var(--white)", lineHeight: 1.25 }}>{label}</div>
        {sub && <div style={{ fontSize: fs - 1.5, color: "var(--t3)", marginTop: 2, lineHeight: 1.35 }}>{sub}</div>}
      </div>
    </div>
  );
}

function Zone({ title, icon: Icon, color, children, width, badge, isPrimary }: {
  title: string; icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>;
  color: string; children: React.ReactNode; width?: number; badge?: string; isPrimary?: boolean;
}) {
  return (
    <div style={{
      border: `${isPrimary ? 2.5 : 2}px solid color-mix(in srgb, ${color} ${isPrimary ? 35 : 22}%, transparent)`,
      borderRadius: 16, background: `color-mix(in srgb, ${color} 2%, var(--bg))`,
      width: width ?? "auto", overflow: "hidden",
      boxShadow: isPrimary
        ? `0 0 50px color-mix(in srgb, ${color} 6%, transparent), 0 4px 24px rgba(0,0,0,0.15)`
        : `0 0 24px color-mix(in srgb, ${color} 3%, transparent)`,
    }}>
      <div style={{ height: isPrimary ? 3 : 2, background: `linear-gradient(90deg, transparent 5%, color-mix(in srgb, ${color} ${isPrimary ? 60 : 40}%, transparent) 50%, transparent 95%)` }} />
      <div style={{
        padding: isPrimary ? "14px 20px" : "10px 16px",
        display: "flex", alignItems: "center", gap: 12,
        borderBottom: `1px solid color-mix(in srgb, ${color} 10%, transparent)`,
      }}>
        <div style={{
          width: isPrimary ? 40 : 34, height: isPrimary ? 40 : 34, borderRadius: 10,
          background: `linear-gradient(135deg, color-mix(in srgb, ${color} 18%, transparent), color-mix(in srgb, ${color} 6%, transparent))`,
          border: `1px solid color-mix(in srgb, ${color} 20%, transparent)`,
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: `0 0 14px color-mix(in srgb, ${color} 10%, transparent)`,
        }}>
          <Icon size={isPrimary ? 20 : 17} color={color} strokeWidth={1.6} />
        </div>
        <div style={{ flex: 1 }}>
          <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: isPrimary ? 15 : 13, color: "var(--white)" }}>{title}</span>
          {badge && <div style={{ fontFamily: "'DM Mono', monospace", fontSize: 9, color: "var(--t4)", marginTop: 1 }}>{badge}</div>}
        </div>
      </div>
      <div style={{ padding: isPrimary ? 18 : 14, display: "flex", flexWrap: "wrap", gap: 10, justifyContent: "center" }}>
        {children}
      </div>
    </div>
  );
}

function Connector({ label, color, direction = "down", dashed }: {
  label: string; color: string; direction?: "down" | "right" | "left"; dashed?: boolean;
}) {
  const isVert = direction === "down";
  const lineLen = isVert ? 28 : 40;
  const lineStyle: React.CSSProperties = {
    width: isVert ? 2 : lineLen, height: isVert ? lineLen : 2,
    background: dashed ? "none" : `color-mix(in srgb, ${color} 35%, transparent)`, borderRadius: 1,
    ...(dashed ? { backgroundImage: `repeating-linear-gradient(${isVert ? "to bottom" : "to right"}, color-mix(in srgb, ${color} 35%, transparent) 0px, color-mix(in srgb, ${color} 35%, transparent) 4px, transparent 4px, transparent 9px)` } : {}),
  };
  const arrows: Record<string, string> = { left: "←", right: "→", down: "↓" };
  return (
    <div style={{ display: "flex", flexDirection: isVert ? "column" : "row", alignItems: "center", gap: 0, padding: isVert ? "4px 0" : "0 4px" }}>
      <div style={lineStyle} />
      <div style={{
        fontFamily: "'DM Mono', monospace", fontSize: 9, fontWeight: 600,
        color: `color-mix(in srgb, ${color} 65%, var(--t3))`,
        padding: "4px 12px", margin: isVert ? "5px 0" : "0 5px",
        border: `1px solid color-mix(in srgb, ${color} 18%, transparent)`,
        borderRadius: 6, background: "var(--bg)", whiteSpace: "nowrap", letterSpacing: "0.03em",
      }}>{label}</div>
      <div style={lineStyle} />
      <div style={{ color: `color-mix(in srgb, ${color} 45%, transparent)`, fontSize: 13, lineHeight: 1, fontWeight: 700 }}>{arrows[direction]}</div>
    </div>
  );
}

function StatPill({ value, label, icon: Icon, color }: {
  value: string; label: string; icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>; color: string;
}) {
  return (
    <div style={{
      background: `color-mix(in srgb, ${color} 4%, var(--bg2))`,
      border: `1px solid color-mix(in srgb, ${color} 15%, transparent)`,
      borderRadius: 12, padding: "16px 24px", textAlign: "center", minWidth: 140, transition: "all 0.2s",
    }}
    onMouseEnter={e => { e.currentTarget.style.borderColor = `color-mix(in srgb, ${color} 35%, transparent)`; }}
    onMouseLeave={e => { e.currentTarget.style.borderColor = `color-mix(in srgb, ${color} 15%, transparent)`; }}
    >
      <div style={{
        width: 36, height: 36, borderRadius: 10, margin: "0 auto 10px",
        background: `linear-gradient(135deg, color-mix(in srgb, ${color} 12%, transparent), color-mix(in srgb, ${color} 5%, transparent))`,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}><Icon size={18} color={color} strokeWidth={1.5} /></div>
      <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 800, fontSize: 20, color: "var(--white)", lineHeight: 1 }}>{value}</div>
      <div style={{ fontSize: 10.5, color: "var(--t3)", marginTop: 4, fontWeight: 500 }}>{label}</div>
    </div>
  );
}

function DeployCard({ label, sub, icon: Icon, color }: {
  label: string; sub: string; icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>; color: string;
}) {
  return (
    <div style={{
      flex: "1 1 0", background: `color-mix(in srgb, ${color} 3%, var(--bg2))`,
      border: `1.5px solid color-mix(in srgb, ${color} 15%, transparent)`,
      borderRadius: 12, padding: "20px 16px", textAlign: "center", transition: "all 0.2s", cursor: "default",
    }}
    onMouseEnter={e => { e.currentTarget.style.transform = "translateY(-3px)"; e.currentTarget.style.borderColor = `color-mix(in srgb, ${color} 40%, transparent)`; }}
    onMouseLeave={e => { e.currentTarget.style.transform = ""; e.currentTarget.style.borderColor = `color-mix(in srgb, ${color} 15%, transparent)`; }}
    >
      <div style={{
        width: 42, height: 42, borderRadius: 11, margin: "0 auto 10px",
        background: `linear-gradient(135deg, color-mix(in srgb, ${color} 12%, transparent), color-mix(in srgb, ${color} 4%, transparent))`,
        border: `1px solid color-mix(in srgb, ${color} 16%, transparent)`,
        display: "flex", alignItems: "center", justifyContent: "center",
      }}><Icon size={20} color={color} strokeWidth={1.5} /></div>
      <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 13, color: "var(--white)" }}>{label}</div>
      <div style={{ fontSize: 10, color: "var(--t3)", marginTop: 3, lineHeight: 1.4 }}>{sub}</div>
    </div>
  );
}

function SecItem({ label, icon: Icon, color }: {
  label: string; icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>; color: string;
}) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, padding: "0 16px" }}>
      <Icon size={15} color={color} strokeWidth={1.6} />
      <span style={{ fontSize: 12, color: "var(--t2)", fontWeight: 500 }}>{label}</span>
    </div>
  );
}

/* ─── MODULE DETAIL CARD ─── */
function ModuleCard({ title, icon: Icon, color, badge, items, pipeline }: {
  title: string;
  icon: React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>;
  color: string;
  badge?: string;
  items: { l: string; s: string }[];
  pipeline?: string[];
}) {
  return (
    <div style={{
      border: `1.5px solid color-mix(in srgb, ${color} 20%, transparent)`,
      borderRadius: 14, background: `color-mix(in srgb, ${color} 2%, var(--bg))`, overflow: "hidden",
    }}>
      <div style={{ height: 2, background: `linear-gradient(90deg, transparent, color-mix(in srgb, ${color} 40%, transparent), transparent)` }} />
      <div style={{
        padding: "10px 16px", borderBottom: `1px solid color-mix(in srgb, ${color} 8%, transparent)`,
        display: "flex", alignItems: "center", gap: 10,
      }}>
        <div style={{
          width: 30, height: 30, borderRadius: 8,
          background: `color-mix(in srgb, ${color} 10%, transparent)`,
          display: "flex", alignItems: "center", justifyContent: "center",
        }}><Icon size={15} color={color} strokeWidth={1.6} /></div>
        <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 12, color: "var(--white)" }}>{title}</span>
        {badge && <span style={{ fontFamily: "'DM Mono', monospace", fontSize: 8, color: "var(--t4)", marginLeft: "auto" }}>{badge}</span>}
      </div>
      <div style={{ padding: 14 }}>
        {pipeline && (
          <div style={{ display: "flex", alignItems: "center", gap: 0, justifyContent: "center", marginBottom: 12 }}>
            {pipeline.map((s, i, a) => (
              <div key={s} style={{ display: "flex", alignItems: "center" }}>
                <div style={{
                  padding: "5px 10px", borderRadius: 6,
                  background: `color-mix(in srgb, ${color} ${i === Math.floor(a.length / 2) ? 12 : 5}%, var(--bg2))`,
                  border: `1px solid color-mix(in srgb, ${color} ${i === Math.floor(a.length / 2) ? 25 : 12}%, transparent)`,
                  fontSize: 9, fontWeight: 600, color: i === Math.floor(a.length / 2) ? color : "var(--t2)", fontFamily: "'Syne'",
                }}>{s}</div>
                {i < a.length - 1 && <div style={{ width: 12, height: 1.5, background: `color-mix(in srgb, ${color} 20%, transparent)`, margin: "0 2px" }} />}
              </div>
            ))}
          </div>
        )}
        <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
          {items.map(x => (
            <div key={x.l} style={{
              padding: "7px 10px", background: `color-mix(in srgb, ${color} 4%, var(--bg2))`,
              border: `1px solid color-mix(in srgb, ${color} 10%, transparent)`, borderRadius: 7,
            }}>
              <div style={{ fontFamily: "'Syne'", fontWeight: 600, fontSize: 10, color: "var(--white)" }}>{x.l}</div>
              <div style={{ fontSize: 8.5, color: "var(--t4)" }}>{x.s}</div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

/* ═══════════════════════════════════════════════════════
   MAIN PAGE
   ═══════════════════════════════════════════════════════ */
export default function TechnicalPage() {
  const [isDark, setIsDark] = useState(true);
  const diagramRef = useRef<HTMLDivElement>(null);

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
    if (!diagramRef.current) return;
    toPng(diagramRef.current, { backgroundColor: isDark ? "#060b16" : "#f8fafc", pixelRatio: 2 }).then(url => {
      const a = document.createElement("a"); a.href = url; a.download = "k-control-architecture.png"; a.click();
    });
  }, [isDark]);

  const blue = "#3b82f6", green = "#10b981", purple = "#a855f7", amber = "#f59e0b",
        indigo = "#6366f1", cyan = "#06b6d4", orange = "#f97316";

  return (
    <div style={{ minHeight: "100vh", background: "var(--bg)", fontFamily: "'DM Sans', sans-serif" }}>

      {/* ═══ NAVBAR ═══ */}
      <div style={{
        height: 56, background: "var(--bg2)", borderBottom: "1px solid var(--brd)",
        display: "flex", alignItems: "center", justifyContent: "space-between", padding: "0 28px",
        position: "sticky", top: 0, zIndex: 10, backdropFilter: "blur(16px)",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div style={{
            width: 34, height: 34, borderRadius: 8,
            background: "linear-gradient(135deg, #1d6ef5, #6366f1)",
            display: "flex", alignItems: "center", justifyContent: "center",
            boxShadow: "0 2px 8px rgba(29,110,245,0.3)",
          }}><Shield size={17} color="#fff" strokeWidth={2} /></div>
          <div>
            <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 15, color: "var(--white)" }}>K-Control</span>
            <span style={{ fontSize: 10, color: "var(--t4)", marginLeft: 8 }}>by Kreesalis</span>
          </div>
          <div style={{ width: 1, height: 22, background: "var(--brd)", margin: "0 8px" }} />
          <span style={{ fontSize: 12, color: "var(--t2)", fontWeight: 500 }}>Technical Architecture</span>
        </div>
        <div style={{ display: "flex", gap: 8 }}>
          <a href="/" style={{
            padding: "7px 16px", borderRadius: 8, border: "1px solid var(--brd)", background: "var(--bg3)",
            color: "var(--t2)", fontSize: 12, textDecoration: "none", display: "flex", alignItems: "center", gap: 6, fontWeight: 500,
          }}><ArrowLeft size={13} /> System View</a>
          <a href="/technical-overview" style={{
            padding: "7px 16px", borderRadius: 8, border: "1px solid var(--brd)", background: "var(--bg3)",
            color: "var(--t2)", fontSize: 12, textDecoration: "none", display: "flex", alignItems: "center", gap: 6, fontWeight: 500,
          }}>Slide View</a>
          <button onClick={exportPng} style={{
            padding: "7px 16px", borderRadius: 8, border: "1px solid var(--brd)", background: "var(--bg3)",
            color: "var(--t2)", fontSize: 12, cursor: "pointer", display: "flex", alignItems: "center", gap: 6, fontWeight: 500,
          }}><Download size={13} /> Export</button>
          <button onClick={toggleTheme} style={{
            width: 38, height: 38, borderRadius: 8, border: "1px solid var(--brd)", background: "var(--bg3)",
            color: "var(--t2)", cursor: "pointer", display: "flex", alignItems: "center", justifyContent: "center",
          }}>{isDark ? <Sun size={15} /> : <Moon size={15} />}</button>
        </div>
      </div>

      {/* ═══ HERO ═══ */}
      <div style={{ padding: "64px 40px 48px", textAlign: "center", position: "relative", overflow: "hidden" }}>
        <div style={{
          position: "absolute", top: "-50%", left: "50%", transform: "translateX(-50%)",
          width: "120%", height: "200%",
          background: `radial-gradient(ellipse at 50% 30%, color-mix(in srgb, ${blue} 6%, transparent) 0%, transparent 60%)`,
          pointerEvents: "none",
        }} />
        <div style={{ position: "relative" }}>
          <div style={{
            display: "inline-flex", alignItems: "center", gap: 6,
            padding: "5px 16px", borderRadius: 20,
            background: `color-mix(in srgb, ${blue} 6%, transparent)`,
            border: `1px solid color-mix(in srgb, ${blue} 15%, transparent)`, marginBottom: 20,
          }}>
            <div style={{ width: 6, height: 6, borderRadius: "50%", background: green, boxShadow: `0 0 8px ${green}` }} />
            <span style={{ fontSize: 11, color: "var(--t2)", fontWeight: 500, letterSpacing: "0.02em" }}>Enterprise Compliance & Governance Platform</span>
          </div>
          <h1 style={{
            fontFamily: "'Syne', sans-serif", fontWeight: 800,
            fontSize: "clamp(28px, 4vw, 42px)", color: "var(--white)",
            letterSpacing: "-0.03em", margin: 0, lineHeight: 1.1,
          }}>K-Control Architecture</h1>
          <p style={{ fontSize: 15, color: "var(--t3)", marginTop: 10, maxWidth: 600, margin: "10px auto 0", lineHeight: 1.6 }}>
            Multi-tenant platform with AI-powered compliance automation,<br />
            continuous monitoring, and deploy-anywhere infrastructure.
          </p>
          <div style={{ display: "flex", justifyContent: "center", gap: 14, marginTop: 32, flexWrap: "wrap" }}>
            <StatPill value="5+" label="Deployment Targets" icon={Cloud} color={blue} />
            <StatPill value="61+" label="API Endpoints" icon={Server} color={green} />
            <StatPill value="27" label="AI Modules" icon={Brain} color={purple} />
            <StatPill value="SSF" label="Compliance Events" icon={Radio} color={amber} />
            <StatPill value="1–5" label="Auto-Scaling Pods" icon={ArrowUpDown} color={cyan} />
          </div>
        </div>
      </div>

      {/* ═══ PLATFORM TOPOLOGY ═══ */}
      <div style={{ padding: "20px 40px 60px", overflowX: "auto" }}>
        <div ref={diagramRef} style={{ minWidth: 1300, display: "flex", flexDirection: "column", alignItems: "center", gap: 0, padding: "20px 0" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
            <Network size={18} color={blue} strokeWidth={1.5} />
            <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 16, color: "var(--white)" }}>Platform Topology</span>
            <div style={{ width: 60, height: 1, background: "var(--brd)" }} />
          </div>

          {/* Row 1: Clients */}
          <Zone title="Clients" icon={Monitor} color={indigo} width={800}>
            <TechBox icon={Globe} label="Web Browser" sub="Server-Rendered · Progressive" color={indigo} />
            <TechBox icon={Smartphone} label="Mobile" sub="iOS · Android" color={indigo} />
            <TechBox icon={Code2} label="REST API" sub="SDKs · Webhooks" color={indigo} />
            <TechBox icon={Radio} label="SSF/CAEP" sub="Security Event Streams" color={indigo} />
          </Zone>
          <Connector label="Encrypted HTTPS" color={indigo} />

          {/* Row 2: Service Mesh */}
          <Zone title="Service Mesh & Edge" icon={Globe} color={blue} width={800} badge="Service Mesh · mTLS · Traffic Management">
            <TechBox icon={Lock} label="TLS Termination" sub="Certificate Management" color={blue} size="sm" />
            <TechBox icon={Shield} label="Mutual TLS" sub="Pod-to-Pod Encryption" color={blue} size="sm" />
            <TechBox icon={Activity} label="Load Balancer" sub="L7 Routing · Weighted" color={blue} size="sm" />
            <TechBox icon={Container} label="Circuit Breaker" sub="Fault Tolerance" color={blue} size="sm" />
            <TechBox icon={Workflow} label="Rate Limiting" sub="Per-Endpoint Throttle" color={blue} size="sm" />
          </Zone>
          <Connector label="Internal Routing" color={blue} />

          {/* Row 3: Main Tier */}
          <div style={{ display: "flex", gap: 16, alignItems: "stretch" }}>
            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <Zone title="Identity & Governance" icon={KeyRound} color={green} width={240}>
                <TechBox icon={ShieldCheck} label="Single Sign-On" sub="OAuth · SAML · Passwordless" color={green} size="sm" />
                <TechBox icon={Users} label="Multi-Tenant" sub="Orgs · Workspaces · Roles" color={green} size="sm" />
                <TechBox icon={AlertTriangle} label="Feature Flags" sub="Environment Gating · Licensing" color={green} size="sm" />
                <TechBox icon={ScrollText} label="Audit Trail" sub="Immutable · Compliance-Ready" color={green} size="sm" />
              </Zone>
            </div>
            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <Connector label="Auth · RBAC" color={green} direction="right" />
            </div>

            <Zone title="K-Control Platform" icon={Shield} color={blue} width={560} badge="Kubernetes · Auto-Scaling · Zero-Downtime" isPrimary>
              <div style={{ display: "flex", gap: 18, width: "100%" }}>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: "'Syne'", fontWeight: 700, fontSize: 9.5, color: "var(--t3)", textTransform: "uppercase", letterSpacing: 2.5, marginBottom: 12, paddingBottom: 8, borderBottom: `1px solid color-mix(in srgb, ${blue} 10%, transparent)` }}>Core Services</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <TechBox icon={LayoutDashboard} label="Web Frontend" sub="Server-Rendered · Responsive UI" color={blue} size="lg" />
                    <TechBox icon={Server} label="API Gateway" sub="Multi-Tenant · 61+ Endpoints" color={green} size="lg" />
                    <TechBox icon={Bell} label="Notifications" sub="Email · Push · In-App · Events" color={cyan} size="lg" />
                  </div>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontFamily: "'Syne'", fontWeight: 700, fontSize: 9.5, color: "var(--t3)", textTransform: "uppercase", letterSpacing: 2.5, marginBottom: 12, paddingBottom: 8, borderBottom: `1px solid color-mix(in srgb, ${blue} 10%, transparent)` }}>Domain Modules</div>
                  <div style={{ display: "flex", flexDirection: "column", gap: 8 }}>
                    <TechBox icon={FlaskConical} label="Compliance Sandbox" sub="Signals · Threats · Policies" color={green} size="lg" />
                    <TechBox icon={BookOpen} label="GRC Library" sub="Frameworks · Controls · Tests" color={indigo} size="lg" />
                    <TechBox icon={Brain} label="AI Copilot" sub="Evidence · Reports · Codegen" color={purple} size="lg" />
                    <TechBox icon={FileCheck} label="Risk Registry" sub="Assess · Track · Mitigate" color={orange} size="lg" />
                  </div>
                </div>
              </div>
            </Zone>

            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <Connector label="AI Requests" color={purple} direction="right" />
            </div>
            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <Zone title="AI & Intelligence" icon={Brain} color={purple} width={240}>
                <TechBox icon={Brain} label="AI Engine" sub="Large Language Models" color={purple} size="sm" />
                <TechBox icon={Search} label="Knowledge Base" sub="Embeddings · RAG · Memory" color={purple} size="sm" />
                <TechBox icon={Eye} label="AI Observability" sub="Cost · Quality · Latency" color={purple} size="sm" />
                <TechBox icon={Bot} label="Agent Runtime" sub="Autonomous AI Agents" color={purple} size="sm" />
              </Zone>
            </div>
          </div>
          <Connector label="Data Access" color={cyan} />

          {/* Row 4: Data Tier */}
          <div style={{ display: "flex", gap: 16, alignItems: "stretch" }}>
            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <Zone title="Observability" icon={Activity} color={amber} width={240}>
                <TechBox icon={RadioTower} label="Telemetry Pipeline" sub="Traces · Metrics · Logs" color={amber} size="sm" />
                <TechBox icon={BarChart3} label="Monitoring" sub="Alerting · SLOs" color={amber} size="sm" />
                <TechBox icon={Layers} label="Distributed Tracing" sub="End-to-End Visibility" color={amber} size="sm" />
                <TechBox icon={Monitor} label="Dashboards" sub="Real-Time · Custom Views" color={amber} size="sm" />
              </Zone>
            </div>
            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <Connector label="Telemetry" color={amber} direction="right" dashed />
            </div>

            <Zone title="Data Layer" icon={Database} color={cyan} width={560} isPrimary>
              <TechBox icon={Database} label="Relational Database" sub="Primary Store · Encrypted" color={green} />
              <TechBox icon={Zap} label="In-Memory Cache" sub="High-Speed · Invalidation" color={cyan} />
              <TechBox icon={BarChart3} label="Analytics Engine" sub="Real-Time · Time-Series" color={amber} />
              <TechBox icon={HardDrive} label="Object Storage" sub="Multi-Provider · Scalable" color={blue} />
            </Zone>

            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <Connector label="Integrations" color={orange} direction="right" dashed />
            </div>
            <div style={{ display: "flex", flexDirection: "column", justifyContent: "center" }}>
              <Zone title="Asset Sources" icon={Boxes} color={orange} width={240}>
                <TechBox icon={Cloud} label="Cloud Platforms" sub="Azure · AWS · GCP · GitHub" color={orange} size="sm" />
                <TechBox icon={Server} label="On-Premises" sub="Self-Hosted · Active Directory" color={orange} size="sm" />
                <TechBox icon={Code2} label="SaaS & APIs" sub="Custom Integrations" color={orange} size="sm" />
                <TechBox icon={ShieldCheck} label="Internal Systems" sub="Configs · Secrets · Flags" color={orange} size="sm" />
              </Zone>
            </div>
          </div>

          {/* Legend */}
          <div style={{
            display: "flex", gap: 32, marginTop: 40, padding: "16px 32px",
            border: "1px solid var(--brd)", borderRadius: 12, background: "var(--bg2)",
          }}>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--t3)" }}>
              <div style={{ width: 28, height: 2, background: `color-mix(in srgb, ${indigo} 45%, transparent)`, borderRadius: 1 }} /> Primary data flow
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--t3)" }}>
              <div style={{ width: 28, height: 2, backgroundImage: `repeating-linear-gradient(to right, color-mix(in srgb, ${amber} 45%, transparent) 0px, color-mix(in srgb, ${amber} 45%, transparent) 4px, transparent 4px, transparent 9px)` }} /> Async / telemetry
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--t3)" }}>
              <div style={{ width: 14, height: 14, borderRadius: 4, border: `2px solid color-mix(in srgb, ${blue} 35%, transparent)` }} /> Primary zone
            </div>
            <div style={{ display: "flex", alignItems: "center", gap: 8, fontSize: 11, color: "var(--t3)" }}>
              <div style={{ width: 14, height: 14, borderRadius: 4, border: `1.5px solid color-mix(in srgb, ${green} 22%, transparent)` }} /> Supporting zone
            </div>
          </div>
        </div>
      </div>

      {/* ═══ REQUEST PIPELINE & MODULE DEEP-DIVE ═══ */}
      <div style={{ padding: "56px 40px 60px", borderTop: "1px solid var(--brd)", overflowX: "auto" }}>
        <div style={{ maxWidth: 1400, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 32 }}>
            <Workflow size={18} color={cyan} strokeWidth={1.5} />
            <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 16, color: "var(--white)" }}>Request Pipeline & Module Architecture</span>
            <div style={{ width: 60, height: 1, background: "var(--brd)" }} />
          </div>

          {/* Request Flow */}
          <div style={{
            border: `2px solid color-mix(in srgb, ${cyan} 20%, transparent)`,
            borderRadius: 16, background: `color-mix(in srgb, ${cyan} 2%, var(--bg))`, overflow: "hidden", marginBottom: 32,
          }}>
            <div style={{ height: 2, background: `linear-gradient(90deg, transparent 5%, color-mix(in srgb, ${cyan} 50%, transparent) 50%, transparent 95%)` }} />
            <div style={{
              padding: "12px 20px", display: "flex", alignItems: "center", gap: 12,
              borderBottom: `1px solid color-mix(in srgb, ${cyan} 10%, transparent)`,
            }}>
              <div style={{
                width: 34, height: 34, borderRadius: 9,
                background: `linear-gradient(135deg, color-mix(in srgb, ${cyan} 15%, transparent), color-mix(in srgb, ${cyan} 5%, transparent))`,
                display: "flex", alignItems: "center", justifyContent: "center",
              }}><Activity size={17} color={cyan} strokeWidth={1.6} /></div>
              <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 13, color: "var(--white)" }}>Request Flow Pipeline</span>
              <span style={{ fontSize: 9, color: "var(--t4)", marginLeft: "auto" }}>
                Client → Edge → Auth → Service → Data → Response
              </span>
            </div>
            <div style={{ padding: 20, overflowX: "auto" }}>
              <div style={{ display: "flex", alignItems: "center", gap: 0, minWidth: 1100 }}>
                {[
                  { label: "Client", sub: "Encrypted Request", icon: Globe, color: indigo, tech: "Browser · Mobile · API" },
                  { label: "Service Mesh", sub: "TLS + mTLS", icon: Lock, color: blue, tech: "Load Balancing · Routing" },
                  { label: "Security Layer", sub: "Headers · CORS", icon: Shield, color: blue, tech: "Content Security Policy" },
                  { label: "Rate Limiter", sub: "Throttle", icon: Gauge, color: amber, tech: "Token Bucket Algorithm" },
                  { label: "Authentication", sub: "Token Validation", icon: KeyRound, color: green, tech: "JWT · Key Rotation" },
                  { label: "Authorization", sub: "Permission Check", icon: Users, color: green, tech: "User → Role → Permission" },
                  { label: "API Router", sub: "Endpoint Match", icon: Server, color: blue, tech: "Validation · Serialization" },
                  { label: "Service Layer", sub: "Business Logic", icon: Workflow, color: purple, tech: "Orchestration · Rules" },
                  { label: "Data Access", sub: "Repository", icon: Database, color: cyan, tech: "Queries · Cache Check" },
                  { label: "Database", sub: "Persist / Read", icon: Database, color: green, tech: "Encrypted · Multi-Schema" },
                ].map((step, i, arr) => (
                  <div key={step.label} style={{ display: "flex", alignItems: "center" }}>
                    <div style={{ display: "flex", flexDirection: "column", alignItems: "center", gap: 6, width: 100, textAlign: "center" }}>
                      <div style={{
                        width: 44, height: 44, borderRadius: 12,
                        background: `linear-gradient(135deg, color-mix(in srgb, ${step.color} 14%, transparent), color-mix(in srgb, ${step.color} 5%, transparent))`,
                        border: `1.5px solid color-mix(in srgb, ${step.color} 22%, transparent)`,
                        display: "flex", alignItems: "center", justifyContent: "center",
                        boxShadow: `0 0 12px color-mix(in srgb, ${step.color} 8%, transparent)`,
                      }}><step.icon size={20} color={step.color} strokeWidth={1.5} /></div>
                      <div>
                        <div style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 10, color: "var(--white)", lineHeight: 1.2 }}>{step.label}</div>
                        <div style={{ fontSize: 8.5, color: step.color, marginTop: 1 }}>{step.sub}</div>
                        <div style={{ fontSize: 8, color: "var(--t4)", marginTop: 2, lineHeight: 1.3 }}>{step.tech}</div>
                      </div>
                    </div>
                    {i < arr.length - 1 && (
                      <div style={{
                        width: 20, height: 2,
                        background: `linear-gradient(to right, color-mix(in srgb, ${step.color} 30%, transparent), color-mix(in srgb, ${arr[i + 1].color} 30%, transparent))`,
                        borderRadius: 1, margin: "0 2px", marginBottom: 36,
                      }} />
                    )}
                  </div>
                ))}
              </div>
            </div>
          </div>

          {/* Module Cards */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            <ModuleCard title="Identity & Access" icon={ShieldCheck} color={green} badge="17 sub-modules" items={[
              { l: "Token Management", s: "Signed tokens · Key rotation · Revocation" },
              { l: "Password Security", s: "Industry-standard hashing · Timing-safe" },
              { l: "Session Management", s: "Multi-device · Concurrent sessions" },
              { l: "Brute Force Protection", s: "Lockout after failed attempts" },
              { l: "Permission Chains", s: "User → Group → Role → Permission" },
              { l: "API Key Management", s: "Scoped · Rotatable · Audited" },
              { l: "Impersonation", s: "Admin access with full audit trail" },
              { l: "Passwordless Auth", s: "Magic links · Time-limited tokens" },
            ]} />

            <ModuleCard title="Compliance Sandbox" icon={FlaskConical} color={green} badge="21 sub-modules"
              pipeline={["Connectors", "Assets", "Datasets", "Signals", "Threats", "Policies", "Libraries"]}
              items={[
                { l: "Sandboxed Execution", s: "Isolated runtime · Resource limits" },
                { l: "Expression Trees", s: "AND/OR/NOT boolean composition" },
                { l: "Credential Encryption", s: "AES-256 · Never stored in plaintext" },
                { l: "Dual-Write Results", s: "Operational DB + Analytics engine" },
                { l: "Event Transmission", s: "SSF/CAEP compliant delivery" },
                { l: "Production Promotion", s: "Sandbox → Control Test Library" },
              ]}
            />

            <ModuleCard title="AI Copilot Platform" icon={Brain} color={purple} badge="27 sub-modules" items={[
              { l: "LLM Integration", s: "Multi-provider · Streaming responses" },
              { l: "Vector Memory", s: "Semantic search · RAG · Embeddings" },
              { l: "Signal Code Generation", s: "AI-generated compliance checks" },
              { l: "Threat Composer", s: "Automated expression tree building" },
              { l: "Evidence Checker", s: "AI-powered compliance verification" },
              { l: "Report Generation", s: "13+ report types · Multi-format" },
              { l: "Framework Builder", s: "Automated GRC framework generation" },
              { l: "Agent Sandbox", s: "Build & deploy autonomous AI agents" },
              { l: "Async Job Queue", s: "Background workers · Concurrency control" },
              { l: "Budget Controls", s: "Per-user and per-org token limits" },
              { l: "Safety Guardrails", s: "Content filters · Compliance checks" },
              { l: "AI Observability", s: "Model performance · Cost tracking" },
            ]} />

            <ModuleCard title="Observability Stack" icon={Activity} color={amber} badge="Full telemetry pipeline"
              pipeline={["Application", "Telemetry Collector", "Processors", "Exporters", "Dashboards"]}
              items={[
                { l: "Metrics Collection", s: "Counters · Histograms · Gauges" },
                { l: "Distributed Tracing", s: "End-to-end request visibility" },
                { l: "Structured Logging", s: "Contextual · Searchable · Retained" },
                { l: "Alerting & SLOs", s: "Threshold & anomaly-based alerts" },
                { l: "Trace-to-Metrics", s: "Auto-generated RED metrics" },
                { l: "Cross-Signal Linking", s: "Logs ↔ Traces ↔ Metrics correlation" },
              ]}
            />
          </div>
        </div>
      </div>

      {/* ═══ DEPLOYMENT ═══ */}
      <div style={{ padding: "48px 40px 56px", borderTop: "1px solid var(--brd)" }}>
        <div style={{ maxWidth: 1300, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 24 }}>
            <Cpu size={18} color={blue} strokeWidth={1.5} />
            <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 16, color: "var(--white)" }}>Deploy Anywhere</span>
            <div style={{ width: 60, height: 1, background: "var(--brd)" }} />
            <span style={{ fontSize: 11, color: "var(--t4)" }}>Flexible infrastructure — cloud, on-premises, or local</span>
          </div>
          <div style={{ display: "flex", gap: 14 }}>
            <DeployCard label="Azure AKS" sub="Managed Kubernetes · Azure Services" icon={Cloud} color="#0078D4" />
            <DeployCard label="Amazon EKS" sub="Managed Kubernetes · AWS Services" icon={Cloud} color="#FF9900" />
            <DeployCard label="Google GKE" sub="Autopilot Kubernetes · GCP Services" icon={Cloud} color="#4285F4" />
            <DeployCard label="On-Premises" sub="Self-Managed Kubernetes" icon={Server} color={green} />
            <DeployCard label="Docker Compose" sub="Local Development · Single Node" icon={Container} color="#2496ED" />
          </div>
          <div style={{
            marginTop: 14, textAlign: "center", color: "var(--t3)", fontSize: 12,
            padding: "12px 20px", border: "1px solid var(--brd)", borderRadius: 10, background: "var(--bg2)",
            fontWeight: 500,
          }}>
            Auto-Scaling &bull; Service Mesh &bull; Rolling Updates &bull; Health Probes &bull; Zero-Downtime &bull; Infrastructure as Code &bull; CI/CD Automation
          </div>
        </div>
      </div>

      {/* ═══ SECURITY ═══ */}
      <div style={{ padding: "40px 40px 56px", borderTop: "1px solid var(--brd)" }}>
        <div style={{ maxWidth: 1300, margin: "0 auto" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 10, marginBottom: 20 }}>
            <Lock size={18} color={green} strokeWidth={1.5} />
            <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 16, color: "var(--white)" }}>Security & Compliance</span>
            <div style={{ width: 60, height: 1, background: "var(--brd)" }} />
          </div>
          <div style={{
            background: "var(--bg2)", border: "1px solid var(--brd)", borderRadius: 14,
            padding: "18px 8px", display: "flex", justifyContent: "space-between", flexWrap: "wrap", gap: 8,
          }}>
            <SecItem label="Encryption at Rest & Transit" icon={Lock} color={green} />
            <div style={{ width: 1, background: "var(--brd)" }} />
            <SecItem label="Token-Based Auth + Key Rotation" icon={KeyRound} color={green} />
            <div style={{ width: 1, background: "var(--brd)" }} />
            <SecItem label="Industry-Standard Password Hashing" icon={ShieldCheck} color={green} />
            <div style={{ width: 1, background: "var(--brd)" }} />
            <SecItem label="Role-Based Access Control" icon={Users} color={green} />
            <div style={{ width: 1, background: "var(--brd)" }} />
            <SecItem label="Rate Limiting & CORS" icon={Gauge} color={green} />
            <div style={{ width: 1, background: "var(--brd)" }} />
            <SecItem label="SSF/CAEP Event Streams" icon={Radio} color={green} />
          </div>
        </div>
      </div>

      {/* ═══ FOOTER ═══ */}
      <footer style={{
        borderTop: "1px solid var(--brd)", padding: "24px 40px",
        display: "flex", alignItems: "center", justifyContent: "space-between",
      }}>
        <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
          <div style={{
            width: 28, height: 28, borderRadius: 7,
            background: "linear-gradient(135deg, #1d6ef5, #6366f1)",
            display: "flex", alignItems: "center", justifyContent: "center",
          }}><Shield size={13} color="#fff" strokeWidth={2} /></div>
          <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 13, color: "var(--white)" }}>K-Control</span>
          <span style={{ fontSize: 10, color: "var(--t4)" }}>by Kreesalis</span>
        </div>
        <div style={{ fontSize: 11, color: "var(--t4)" }}>&copy; 2026 Kreesalis. All rights reserved.</div>
        <a href="/" style={{ fontSize: 11, color: "var(--t3)", textDecoration: "none", display: "flex", alignItems: "center", gap: 4 }}>
          System View <ChevronRight size={12} />
        </a>
      </footer>
    </div>
  );
}
