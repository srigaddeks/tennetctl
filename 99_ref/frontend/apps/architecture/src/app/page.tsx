"use client";

import { useCallback, useEffect, useState } from "react";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  BackgroundVariant,
  type NodeTypes,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { toPng } from "html-to-image";
import { Shield, Sun, Moon, Download, ArrowRight } from "lucide-react";
import ZoneNode from "@/components/ZoneNode";
import { nodes as initialNodes, edges as initialEdges } from "@/lib/diagram-data";

const nodeTypes: NodeTypes = {
  zone: ZoneNode as unknown as NodeTypes["zone"],
};

export default function ArchitecturePage() {
  const [nodes, , onNodesChange] = useNodesState(initialNodes);
  const [edges, , onEdgesChange] = useEdgesState(initialEdges);
  const [isDark, setIsDark] = useState(true);

  useEffect(() => {
    const saved = localStorage.getItem("kc-arch-theme");
    if (saved === "light") {
      setIsDark(false);
      document.documentElement.classList.add("light");
    }
  }, []);

  const toggleTheme = useCallback(() => {
    setIsDark((prev) => {
      const next = !prev;
      document.documentElement.classList.toggle("light", next);
      localStorage.setItem("kc-arch-theme", next ? "light" : "dark");
      return next;
    });
  }, []);

  const exportPng = useCallback(() => {
    const el = document.querySelector(".react-flow") as HTMLElement;
    if (!el) return;
    toPng(el, {
      backgroundColor: isDark ? "#060b16" : "#f8fafc",
      pixelRatio: 2,
    }).then((dataUrl) => {
      const a = document.createElement("a");
      a.href = dataUrl;
      a.download = "k-control-system-architecture.png";
      a.click();
    });
  }, [isDark]);

  return (
    <div style={{ width: "100vw", height: "100vh", background: "var(--bg)", display: "flex", flexDirection: "column" }}>
      {/* Top bar */}
      <div
        style={{
          height: 56,
          minHeight: 56,
          background: "var(--bg2)",
          borderBottom: "1px solid var(--brd)",
          display: "flex",
          alignItems: "center",
          justifyContent: "space-between",
          padding: "0 24px",
          zIndex: 10,
        }}
      >
        <div style={{ display: "flex", alignItems: "center", gap: 12 }}>
          <div
            style={{
              width: 32,
              height: 32,
              borderRadius: 7,
              background: "linear-gradient(135deg, #1d6ef5, #6366f1)",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            <Shield size={16} color="#fff" strokeWidth={2} />
          </div>
          <span style={{ fontFamily: "'Syne', sans-serif", fontWeight: 700, fontSize: 15, color: "var(--white)" }}>
            K-Control
          </span>
          <div style={{ width: 1, height: 20, background: "var(--brd)", margin: "0 4px" }} />
          <span style={{ fontSize: 12, color: "var(--t2)", fontWeight: 500 }}>System Architecture</span>
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
          <a
            href="/technical"
            style={{
              padding: "6px 14px",
              borderRadius: 7,
              border: "1px solid var(--brd)",
              background: "var(--bg3)",
              color: "var(--t2)",
              fontSize: 12,
              fontFamily: "'DM Sans', sans-serif",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              textDecoration: "none",
              transition: "all 0.15s",
            }}
          >
            Technical View <ArrowRight size={12} />
          </a>
          <a
            href="/slide"
            style={{
              padding: "6px 14px",
              borderRadius: 7,
              border: "1px solid var(--brd)",
              background: "var(--bg3)",
              color: "var(--t2)",
              fontSize: 12,
              fontFamily: "'DM Sans', sans-serif",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
              textDecoration: "none",
              transition: "all 0.15s",
            }}
          >
            Slide View <ArrowRight size={12} />
          </a>
          <button
            onClick={exportPng}
            style={{
              padding: "6px 14px",
              borderRadius: 7,
              border: "1px solid var(--brd)",
              background: "var(--bg3)",
              color: "var(--t2)",
              fontSize: 12,
              fontFamily: "'DM Sans', sans-serif",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              gap: 6,
            }}
          >
            <Download size={13} /> Export PNG
          </button>
          <button
            onClick={toggleTheme}
            style={{
              width: 36,
              height: 36,
              borderRadius: 8,
              border: "1px solid var(--brd)",
              background: "var(--bg3)",
              color: "var(--t2)",
              cursor: "pointer",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
            }}
          >
            {isDark ? <Sun size={15} /> : <Moon size={15} />}
          </button>
        </div>
      </div>

      {/* React Flow canvas */}
      <div style={{ flex: 1 }}>
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          nodeTypes={nodeTypes}
          fitView
          fitViewOptions={{ padding: 0.12 }}
          minZoom={0.2}
          maxZoom={2.5}
          proOptions={{ hideAttribution: true }}
          elevateEdgesOnSelect={false}
          style={{ zIndex: 0 }}
        >
          <Background variant={BackgroundVariant.Dots} gap={20} size={1} color={isDark ? "#1a2c4a" : "#e2e8f0"} />
          <Controls showInteractive={false} />
          <MiniMap
            nodeColor={(n) => {
              const data = n.data as { color?: string };
              return data?.color ?? "#475569";
            }}
            maskColor={isDark ? "rgba(6,11,22,0.8)" : "rgba(248,250,252,0.8)"}
          />
        </ReactFlow>
      </div>
    </div>
  );
}
