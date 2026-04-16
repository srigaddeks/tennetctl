"use client"

import * as React from "react"
import { cn } from "../../../lib/utils"
import { SidebarTrigger } from "../sidebar"
import { Separator } from "../separator"

export interface TopbarProps extends React.ComponentProps<"header"> {
  title?: string
  logo?: React.ReactNode
  actions?: React.ReactNode
}

export function Topbar({
  className,
  title,
  logo,
  actions,
  children,
  ...props
}: TopbarProps) {
  return (
    <header
      className={cn(
        "sticky top-0 z-30 flex h-14 w-full shrink-0 items-center justify-between border-b border-border bg-background/60 px-4 backdrop-blur-lg transition-all duration-200",
        className
      )}
      {...props}
    >
      <div className="flex items-center gap-3">
        <SidebarTrigger className="-ml-1 h-8 w-8 hover:bg-accent" />
        <Separator orientation="vertical" className="h-4" />
        <div className="flex items-center gap-3">
          {logo}
          {title && (
            <h1 className="text-sm font-semibold tracking-tight sm:text-base font-secondary">
              {title}
            </h1>
          )}
          {children}
        </div>
      </div>

      {actions && (
        <div className="flex items-center gap-2">
          {actions}
        </div>
      )}
    </header>
  )
}
