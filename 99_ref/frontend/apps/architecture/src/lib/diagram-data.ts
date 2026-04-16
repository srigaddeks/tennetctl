import type { Node, Edge } from "@xyflow/react";
import type { ZoneNodeData } from "@/components/ZoneNode";

export const nodes: Node<ZoneNodeData>[] = [
  {
    id: "clients",
    type: "zone",
    position: { x: 0, y: 120 },
    data: {
      label: "Clients",
      icon: "monitor",
      color: "#6366f1",
      richItems: [
        { name: "Web Application", desc: "Server-Rendered · Responsive · Progressive", icon: "globe" },
        { name: "Mobile Apps", desc: "iOS · Android · Cross-Platform", icon: "smartphone" },
        { name: "API Consumers", desc: "REST Integrations · Webhooks · SDKs", icon: "code" },
        { name: "Event Receivers", desc: "SSF/CAEP Compliance Streams", icon: "radio" },
      ],
    },
  },
  {
    id: "platform",
    type: "zone",
    position: { x: 380, y: 0 },
    data: {
      label: "K-Control Platform",
      icon: "shield",
      color: "#3b82f6",
      badge: "Kubernetes · Service Mesh · Auto-Scaling",
      width: 580,
      columns: [
        {
          title: "Core Services",
          items: [
            { name: "Web Frontend", desc: "Server-Side Rendered · SPA", icon: "dashboard" },
            { name: "API Gateway", desc: "Multi-Tenant · 61+ Endpoints", icon: "server" },
            { name: "Auth & RBAC", desc: "SSO · MFA · Permission Chains", icon: "shield-check" },
            { name: "Notifications", desc: "Email · Push · In-App · Events", icon: "bell" },
          ],
        },
        {
          title: "Domain Modules",
          items: [
            { name: "Compliance Sandbox", desc: "Signals · Threats · Policies", icon: "flask" },
            { name: "GRC Library", desc: "Frameworks · Controls · Tests", icon: "book" },
            { name: "AI Copilot", desc: "Evidence · Reports · Codegen", icon: "brain" },
            { name: "Risk Registry", desc: "Assess · Track · Mitigate", icon: "alert" },
          ],
        },
      ],
    },
  },
  {
    id: "assets",
    type: "zone",
    position: { x: 1080, y: 0 },
    data: {
      label: "Asset Sources",
      icon: "boxes",
      color: "#f97316",
      richItems: [
        { name: "Cloud Platforms", desc: "Azure · AWS · GCP · GitHub", icon: "cloud" },
        { name: "On-Premises", desc: "Self-Hosted · Active Directory · LDAP", icon: "server" },
        { name: "SaaS & Third-Party", desc: "Custom Integrations · APIs", icon: "code" },
        { name: "Internal Assets", desc: "Configurations · Secrets · Flags", icon: "shield-check" },
      ],
    },
  },
  {
    id: "identity",
    type: "zone",
    position: { x: 0, y: 480 },
    data: {
      label: "Identity & Governance",
      icon: "key",
      color: "#10b981",
      richItems: [
        { name: "Single Sign-On", desc: "OAuth · SAML · Passwordless", icon: "user-check" },
        { name: "Multi-Tenant Isolation", desc: "Organizations · Workspaces · Roles", icon: "users" },
        { name: "Feature Management", desc: "Environment Gating · Licensing", icon: "shield-alert" },
        { name: "Audit Trail", desc: "Immutable · Compliance-Ready", icon: "scroll" },
      ],
    },
  },
  {
    id: "data",
    type: "zone",
    position: { x: 380, y: 530 },
    data: {
      label: "Data Layer",
      icon: "database",
      color: "#06b6d4",
      width: 580,
      richItems: [
        { name: "Relational Database", desc: "Primary Store · Encrypted at Rest", icon: "database" },
        { name: "In-Memory Cache", desc: "High-Speed Reads · Pattern Invalidation", icon: "zap" },
        { name: "Analytics Engine", desc: "Real-Time · Time-Series · OLAP", icon: "chart" },
        { name: "Object Storage", desc: "Multi-Provider · S3 / GCS / Azure / MinIO", icon: "hard-drive" },
      ],
    },
  },
  {
    id: "ai",
    type: "zone",
    position: { x: 1080, y: 340 },
    data: {
      label: "AI & Intelligence",
      icon: "sparkles",
      color: "#a855f7",
      richItems: [
        { name: "AI Engine", desc: "Large Language Models · Streaming", icon: "brain" },
        { name: "Knowledge Base", desc: "Embeddings · RAG · Semantic Memory", icon: "search" },
        { name: "AI Observability", desc: "Model Performance · Cost Tracking", icon: "eye" },
        { name: "Asset Collector", desc: "Cloud & On-Prem Discovery", icon: "scan" },
      ],
    },
  },
  {
    id: "obs",
    type: "zone",
    position: { x: 0, y: 820 },
    data: {
      label: "Observability",
      icon: "activity",
      color: "#f59e0b",
      richItems: [
        { name: "Telemetry Pipeline", desc: "Traces · Metrics · Structured Logs", icon: "tower" },
        { name: "Monitoring", desc: "Alerting · SLOs · Dashboards", icon: "chart" },
        { name: "Distributed Tracing", desc: "End-to-End Request Visibility", icon: "activity" },
        { name: "Dashboards", desc: "Real-Time · Custom Views · Alerts", icon: "monitor" },
      ],
    },
  },
];

// Edge builder
function edge(
  id: string, source: string, target: string, label: string, color: string,
  opts?: { dash?: boolean; animated?: boolean; srcH?: string; tgtH?: string }
): Edge {
  return {
    id, source, target, label,
    type: "default",
    sourceHandle: opts?.srcH,
    targetHandle: opts?.tgtH,
    style: {
      stroke: color,
      strokeWidth: opts?.dash ? 1.5 : 2,
      ...(opts?.dash ? { strokeDasharray: "8 5" } : {}),
    },
    labelStyle: {
      fill: color,
      fontSize: 10,
      fontFamily: "'DM Mono', monospace",
      fontWeight: 600,
      letterSpacing: "0.02em",
    },
    labelBgStyle: {
      stroke: color,
      strokeWidth: 1,
      rx: 6,
      ry: 6,
    },
    labelBgPadding: [10, 6] as [number, number],
    animated: opts?.animated,
  };
}

export const edges: Edge[] = [
  // Solid lines — primary data flows
  edge("e1", "clients", "platform", "HTTPS · Encrypted", "#6366f1", { animated: true }),
  edge("e2", "identity", "platform", "Auth · RBAC", "#10b981"),
  edge("e3", "platform", "data", "Read · Write", "#06b6d4", { srcH: "bottom", tgtH: "top" }),
  edge("e4", "platform", "ai", "AI Requests", "#a855f7"),
  edge("e5", "platform", "assets", "Discovery", "#f97316"),

  // Dashed lines — secondary / async flows
  edge("e6", "platform", "obs", "Telemetry", "#f59e0b", { dash: true, srcH: "bottom", tgtH: "top" }),
  edge("e7", "data", "ai", "Knowledge · Embeddings", "#a855f7", { dash: true }),
  edge("e8", "obs", "data", "Metrics Store", "#f59e0b", { dash: true }),
  edge("e9", "identity", "data", "User Store", "#10b981", { dash: true, srcH: "bottom", tgtH: "top" }),
  edge("e10", "assets", "ai", "Asset Feed", "#f97316", { dash: true, srcH: "bottom", tgtH: "top" }),
];
