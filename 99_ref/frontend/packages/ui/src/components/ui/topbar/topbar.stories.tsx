import type { Meta, StoryObj } from "@storybook/react"
import React from "react"
import { Topbar } from "./topbar"
import { SidebarProvider, SidebarInset } from "../sidebar"
import { AppSidebar } from "../sidebar/app-sidebar"
import { ThemeToggle } from "../theme-toggle"
import { Logo } from "../logo"

const meta: Meta<typeof Topbar> = {
  title: "Components/Layout/Topbar",
  component: Topbar,
  parameters: {
    layout: "fullscreen",
  },
  decorators: [
    (Story) => (
      <div className="h-screen overflow-hidden">
        <SidebarProvider>
          <AppSidebar />
          <SidebarInset>
            <Story />
            <div className="p-6">
              <div className="grid gap-4 md:grid-cols-2 lg:grid-cols-4">
                {[...Array(4)].map((_, i) => (
                  <div
                    key={i}
                    className="aspect-video rounded-xl border border-border bg-muted/50 p-4"
                  >
                    <div className="h-full w-full rounded-lg bg-background/50" />
                  </div>
                ))}
              </div>
            </div>
          </SidebarInset>
        </SidebarProvider>
      </div>
    ),
  ],
}

export default meta
type Story = StoryObj<typeof Topbar>

export const Default: Story = {
  args: {
    logo: <Logo className="h-6 w-auto" />,
    actions: (
      <>
        <ThemeToggle />
      </>
    ),
  },
}

export const Simple: Story = {
  args: {
    title: "Settings",
    actions: <ThemeToggle />,
  },
}
