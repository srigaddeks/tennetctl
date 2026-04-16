"use client";

import { memo } from "react";
import { Handle, Position, type NodeProps } from "@xyflow/react";
import {
  Monitor, Globe, Smartphone, Code2, Radio, Shield, Server, ShieldCheck,
  Bell, FlaskConical, BookOpen, Brain, Bot, Cloud, KeyRound,
  UserCheck, Users, ScrollText, Database, Zap, BarChart3, HardDrive,
  Sparkles, Search, Eye, ScanSearch, Activity, RadioTower, LayoutDashboard,
  Lock, Gauge, FileCheck, GitBranch, ShieldAlert, Library, Wand2, Mail,
  Container, AlertTriangle, FileOutput, Boxes,
} from "lucide-react";

export interface ZoneNodeData extends Record<string, unknown> {
  label: string;
  icon?: string;
  color: string;
  richItems?: { name: string; desc?: string; icon?: string }[];
  columns?: {
    title: string;
    items: { name: string; desc?: string; icon?: string }[];
  }[];
  badge?: string;
  width?: number;
  variant?: "primary" | "outline";
}

const ICONS: Record<string, React.ComponentType<{ size?: number; color?: string; strokeWidth?: number }>> = {
  monitor: Monitor, globe: Globe, smartphone: Smartphone, code: Code2,
  radio: Radio, shield: Shield, server: Server, "shield-check": ShieldCheck,
  bell: Bell, flask: FlaskConical, book: BookOpen, brain: Brain, bot: Bot,
  cloud: Cloud, key: KeyRound, "user-check": UserCheck,
  users: Users, scroll: ScrollText, database: Database, zap: Zap,
  chart: BarChart3, "hard-drive": HardDrive, sparkles: Sparkles,
  search: Search, eye: Eye, scan: ScanSearch, activity: Activity,
  tower: RadioTower, dashboard: LayoutDashboard, lock: Lock, gauge: Gauge,
  "file-check": FileCheck, "git-branch": GitBranch, "shield-alert": ShieldAlert,
  library: Library, wand: Wand2, mail: Mail, container: Container,
  alert: AlertTriangle, "file-output": FileOutput, boxes: Boxes,
};

function Ico({ name, color = "#fff", size = 16 }: { name?: string; color?: string; size?: number }) {
  if (!name) return null;
  const C = ICONS[name];
  return C ? <C size={size} color={color} strokeWidth={1.6} /> : null;
}

function hex(h: string, a: number) {
  const r = parseInt(h.slice(1, 3), 16), g = parseInt(h.slice(3, 5), 16), b = parseInt(h.slice(5, 7), 16);
  return `rgba(${r},${g},${b},${a})`;
}

function ItemRow({ name, desc, icon, color }: { name: string; desc?: string; icon?: string; color: string }) {
  return (
    <div style={{
      display: "flex", alignItems: "center", gap: 10,
      padding: "9px 12px",
      background: hex(color, 0.04),
      border: `1px solid ${hex(color, 0.1)}`,
      borderRadius: 8,
    }}>
      {icon && (
        <div style={{
          width: 30, height: 30, borderRadius: 8,
          background: hex(color, 0.08),
          border: `1px solid ${hex(color, 0.12)}`,
          display: "flex", alignItems: "center", justifyContent: "center",
          flexShrink: 0,
        }}>
          <Ico name={icon} color={color} size={14} />
        </div>
      )}
      <div style={{ minWidth: 0 }}>
        <div style={{
          fontFamily: "'Syne', sans-serif", fontWeight: 600,
          fontSize: 11.5, color: "var(--white)", lineHeight: 1.3,
        }}>{name}</div>
        {desc && <div style={{ fontSize: 9.5, color: "var(--t3)", lineHeight: 1.3, marginTop: 1 }}>{desc}</div>}
      </div>
    </div>
  );
}

function ZoneNode({ data }: NodeProps & { data: ZoneNodeData }) {
  const { label, icon, color, richItems, columns, badge, width } = data;

  const handleStyle = {
    background: color,
    border: `2px solid ${hex(color, 0.25)}`,
    width: 10, height: 10,
    boxShadow: `0 0 8px ${hex(color, 0.3)}`,
  };

  return (
    <div style={{
      background: hex(color, 0.02),
      border: `1.5px solid ${hex(color, 0.25)}`,
      borderRadius: 14,
      minWidth: width ?? 250,
      fontFamily: "'DM Sans', sans-serif",
      position: "relative",
      backdropFilter: "blur(8px)",
      boxShadow: `0 0 30px ${hex(color, 0.04)}, 0 1px 2px rgba(0,0,0,0.2)`,
    }}>
      {/* Accent top line */}
      <div style={{
        position: "absolute", top: 0, left: 20, right: 20, height: 1,
        background: `linear-gradient(90deg, transparent, ${hex(color, 0.4)}, transparent)`,
      }} />

      <Handle type="target" position={Position.Left} style={handleStyle} />
      <Handle type="source" position={Position.Right} style={handleStyle} />
      <Handle type="target" position={Position.Top} id="top" style={handleStyle} />
      <Handle type="source" position={Position.Bottom} id="bottom" style={handleStyle} />

      {/* Header */}
      <div style={{
        padding: "14px 18px 12px",
        display: "flex", alignItems: "center", gap: 12,
        borderBottom: `1px solid ${hex(color, 0.1)}`,
      }}>
        {icon && (
          <div style={{
            width: 38, height: 38, borderRadius: 10,
            background: `linear-gradient(135deg, ${hex(color, 0.15)}, ${hex(color, 0.05)})`,
            border: `1px solid ${hex(color, 0.2)}`,
            display: "flex", alignItems: "center", justifyContent: "center",
            flexShrink: 0,
            boxShadow: `0 0 12px ${hex(color, 0.1)}`,
          }}>
            <Ico name={icon} color={color} size={20} />
          </div>
        )}
        <div style={{ flex: 1 }}>
          <div style={{
            fontFamily: "'Syne', sans-serif", fontWeight: 700,
            fontSize: 14, color: "var(--white)", letterSpacing: "-0.01em",
          }}>{label}</div>
          {badge && (
            <div style={{
              fontFamily: "'DM Mono', monospace", fontSize: 9,
              color: hex(color, 0.6), marginTop: 2,
            }}>{badge}</div>
          )}
        </div>
      </div>

      {/* Body */}
      <div style={{ padding: "12px 16px 16px" }}>

        {/* Rich items */}
        {richItems && (
          <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
            {richItems.map((item) => (
              <ItemRow key={item.name} name={item.name} desc={item.desc} icon={item.icon} color={color} />
            ))}
          </div>
        )}

        {/* Two-column sections */}
        {columns && (
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16 }}>
            {columns.map((col) => (
              <div key={col.title}>
                <div style={{
                  fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 9,
                  color: hex(color, 0.45), textTransform: "uppercase", letterSpacing: 2,
                  marginBottom: 8, paddingBottom: 6,
                  borderBottom: `1px solid ${hex(color, 0.08)}`,
                }}>{col.title}</div>
                <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                  {col.items.map((item) => (
                    <ItemRow key={item.name} name={item.name} desc={item.desc} icon={item.icon} color={color} />
                  ))}
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}

export default memo(ZoneNode);
