"use client";

import "react-grid-layout/css/styles.css";
import "react-resizable/css/styles.css";

import {
  ResponsiveGridLayout,
  useContainerWidth,
  type Layout,
  type LayoutItem,
  type ResponsiveLayouts,
} from "react-grid-layout";

import type { Panel as PanelT } from "@/types/api";

import { Panel } from "./panel";

export type DashboardLayouts = ResponsiveLayouts<string>;

type Props = {
  panels: PanelT[];
  editing: boolean;
  onLayoutChange?: (layouts: DashboardLayouts) => void;
};

export function DashboardGrid({ panels, editing, onLayoutChange }: Props) {
  const { width, containerRef, mounted } = useContainerWidth();

  const lgItems: LayoutItem[] = panels.map((p) => ({
    i: p.id,
    x: p.grid_pos?.x ?? 0,
    y: p.grid_pos?.y ?? 0,
    w: p.grid_pos?.w ?? 4,
    h: p.grid_pos?.h ?? 4,
    minW: 2,
    minH: 2,
  }));

  const layouts: DashboardLayouts = {
    lg: lgItems,
    md: lgItems,
    sm: lgItems,
    xs: lgItems,
    xxs: lgItems,
  };

  return (
    <div ref={containerRef} data-testid="monitoring-dashboard-grid">
      {mounted && (
        <ResponsiveGridLayout
          width={width}
          layouts={layouts}
          breakpoints={{ lg: 1200, md: 996, sm: 768, xs: 480, xxs: 0 }}
          cols={{ lg: 12, md: 10, sm: 6, xs: 4, xxs: 2 }}
          rowHeight={60}
          dragConfig={{ enabled: editing, bounded: false }}
          resizeConfig={{ enabled: editing, handles: ["se"] }}
          onLayoutChange={(_layout: Layout, all: DashboardLayouts) => {
            onLayoutChange?.(all);
          }}
        >
          {panels.map((p) => (
            <div key={p.id}>
              <Panel panel={p} />
            </div>
          ))}
        </ResponsiveGridLayout>
      )}
    </div>
  );
}
