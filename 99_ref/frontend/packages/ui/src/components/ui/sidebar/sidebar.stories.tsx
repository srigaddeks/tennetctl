import * as React from "react";
import type { Meta, StoryObj } from "@storybook/react";
import { AppSidebar } from "./app-sidebar";
import {
  SidebarProvider,
  SidebarInset,
  SidebarTrigger,
  useSidebar,
} from "./sidebar";

/**
 * Inner layout component — must live inside <SidebarProvider> to access useSidebar().
 * Renders the trigger button in the main content header, hidden when the sidebar
 * is collapsed (since the sidebar itself is fully off screen at that point).
 */
function AppLayout() {
  return (
    <>
      <AppSidebar />
      <SidebarInset>
        {/* Sticky top bar — trigger always visible outside the sidebar */}
        <header className="sticky top-0 z-10 flex h-12 items-center gap-3 border-b border-border bg-background/80 px-4 backdrop-blur-sm">
          <SidebarTrigger />
          <span className="text-sm font-medium text-muted-foreground">
            Dashboard
          </span>
        </header>

        {/* Page content */}
        <div className="p-6">
          <h1 className="text-2xl font-bold">Main Content</h1>
          <p className="mt-2 text-muted-foreground">
            The toggle button lives in the header above — outside the sidebar.
            Click it to collapse or expand the sidebar.
          </p>
        </div>
      </SidebarInset>
    </>
  );
}

const meta: Meta<typeof AppSidebar> = {
  title: "Components/Sidebar/AppSidebar",
  component: AppSidebar,
  parameters: {
    layout: "fullscreen",
  },
  decorators: [
    () => (
      <div className="h-screen overflow-hidden">
        <SidebarProvider>
          <AppLayout />
        </SidebarProvider>
      </div>
    ),
  ],
};

export default meta;
type Story = StoryObj<typeof AppSidebar>;

export const Default: Story = {
  render: () => <AppLayout />,
};
