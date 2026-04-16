"use client"

import * as React from "react"
import {
  User,
  Lock,
  Bell,
  Palette,
  ArrowLeft,
  ClipboardList,
} from "lucide-react"

import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  SidebarHeader,
  SidebarRail,
} from "./sidebar"
import { useBrowserPathname } from "./use-browser-pathname"

const settingsSidebarItems = [
  {
    title: "Profile",
    url: "/settings/profile",
    icon: User,
  },
  {
    title: "Security",
    url: "/settings/security",
    icon: Lock,
  },
  {
    title: "Notifications",
    url: "/settings/notifications",
    icon: Bell,
  },
  {
    title: "Appearance",
    url: "/settings/appearance",
    icon: Palette,
  },
  {
    title: "Questionnaire",
    url: "/settings/questionnaire",
    icon: ClipboardList,
  },
]

function normalizePath(path: string): string {
  if (!path) return "/"
  return path.length > 1 && path.endsWith("/") ? path.slice(0, -1) : path
}

function isPathMatch(pathname: string, url: string): boolean {
  const currentPath = normalizePath(pathname)
  const targetPath = normalizePath(url)

  return currentPath === targetPath || currentPath.startsWith(`${targetPath}/`)
}

function getActiveUrl(pathname: string, urls: string[]): string | null {
  const matchingUrls = urls
    .map((url) => normalizePath(url))
    .filter((url) => isPathMatch(pathname, url))
    .sort((left, right) => right.length - left.length)

  return matchingUrls[0] ?? null
}

export function SettingsSidebar({ currentPath }: { currentPath?: string } = {}) {
  const pathname = useBrowserPathname(currentPath)
  const activeUrl = React.useMemo(
    () => getActiveUrl(pathname ?? "/", settingsSidebarItems.map((item) => item.url)),
    [pathname],
  )

  return (
    <Sidebar
      variant="sidebar"
      collapsible="offcanvas"
    >
      <SidebarHeader className="border-b border-sidebar-border p-4">
        <SidebarMenu>
          <SidebarMenuItem>
            <SidebarMenuButton asChild size="lg" className="hover:bg-transparent">
              <a href="/dashboard">
                <div className="flex aspect-square size-8 items-center justify-center rounded-lg bg-sidebar-primary text-sidebar-primary-foreground">
                  <ArrowLeft className="size-4" />
                </div>
                <div className="flex flex-col gap-0.5 leading-none">
                  <span className="font-semibold">Back to Dashboard</span>
                </div>
              </a>
            </SidebarMenuButton>
          </SidebarMenuItem>
        </SidebarMenu>
      </SidebarHeader>
      <SidebarContent>
        <SidebarGroup>
          <SidebarGroupLabel>Settings</SidebarGroupLabel>
          <SidebarGroupContent>
            <SidebarMenu>
              {settingsSidebarItems.map((item) => (
                <SidebarMenuItem key={item.title}>
                  <SidebarMenuButton asChild isActive={activeUrl === normalizePath(item.url)}>
                    <a href={item.url} aria-current={activeUrl === normalizePath(item.url) ? "page" : undefined}>
                      <item.icon />
                      <span>{item.title}</span>
                    </a>
                  </SidebarMenuButton>
                </SidebarMenuItem>
              ))}
            </SidebarMenu>
          </SidebarGroupContent>
        </SidebarGroup>
      </SidebarContent>
      <SidebarRail />
    </Sidebar>
  )
}
