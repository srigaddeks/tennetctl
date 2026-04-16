"use client"

import { useView, ViewDefinition } from "@/lib/context/ViewContext"
import { cn } from "@kcontrol/ui"
import { useRef, useEffect } from "react"
import {
  Globe,
  ShieldCheck,
  Search,
  LayoutDashboard,
  Building2,
  ChevronDown,
  Check,
  Activity,
  UserCircle,
  LucideIcon
} from "lucide-react"
import {
  Sheet,
  SheetContent,
  SheetDescription,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
} from "@kcontrol/ui"

/**
 * Dynamic Icon Map - Fallbacks to Activity if not found
 */
const ICON_MAP: Record<string, LucideIcon> = {
  "Globe": Globe,
  "ShieldCheck": ShieldCheck,
  "Search": Search,
  "LayoutDashboard": LayoutDashboard,
  "Building2": Building2,
  "Practitioner": ShieldCheck,
  "Auditor": Search,
  "Executive": Building2,
  "Vendor": UserCircle,
}

function ViewIcon({ name, label, className, style }: { name: string | null, label: string, className?: string, style?: React.CSSProperties }) {
  // If icon-name is provided, try to find it. Otherwise, try to find one based on the label.
  const Icon = (name && ICON_MAP[name]) || ICON_MAP[label] || Activity
  return <Icon className={className} style={style} />
}

export function ViewBar() {
  const { availableViews, activeView, activeViewDef, setActiveView, ready } = useView()
  const scrollContainerRef = useRef<HTMLDivElement>(null)
  const activeItemRef = useRef<HTMLButtonElement>(null)

  // Suggestion: If roles > 6, we use a more compact layout on desktop too
  const isLargeList = availableViews.length > 5

  // Auto-scroll logic: Keep the active role in view
  useEffect(() => {
    if (activeItemRef.current && scrollContainerRef.current) {
      activeItemRef.current.scrollIntoView({
        behavior: "smooth",
        block: "nearest",
        inline: "center",
      })
    }
  }, [activeView])

  if (!ready || availableViews.length <= 1) return null

  return (
    <div
      className="relative flex items-center justify-between gap-4 px-6 py-1.5 border-b bg-card/40 backdrop-blur-[20px] shrink-0 transition-all duration-700 ease-in-out overflow-hidden"
      style={{
        borderTop: `1px solid ${activeViewDef.color}66`,
        backgroundColor: `${activeViewDef.color}05`
      }}
    >
      <div className="flex items-center gap-4 w-full max-w-[1600px] mx-auto">

        {/* LEFT: Context Branding (Ultra-Slim) */}
        <div className="flex items-center gap-2.5 shrink-0 lg:border-r lg:border-border/20 lg:pr-6">
          <div className="relative flex h-2 w-2">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full opacity-30" style={{ backgroundColor: activeViewDef.color }}></span>
            <span className="relative inline-flex rounded-full h-2 w-2 shadow-sm" style={{ backgroundColor: activeViewDef.color }}></span>
          </div>
          <div className="hidden lg:flex items-baseline gap-2">
            <span className="text-[9px] font-black uppercase tracking-[0.2em] text-muted-foreground/50 whitespace-nowrap">
              Viewing As
            </span>
          </div>
          {/* Mobile/Tablet simple label */}
          <span className="text-[10px] font-black uppercase tracking-[0.1em] text-foreground/60 lg:hidden">
            Viewing As
          </span>
        </div>

        {/* MIDDLE: Adaptive Role Tray (Slim) */}
        <div className="flex-1 flex justify-center min-w-0">
          {/* DESKTOP: Slim Capsule */}
          <div className="hidden md:flex items-center p-0.5 bg-background/40 rounded-full border border-border/30 shadow-sm backdrop-blur-xl relative max-w-full group">
            <div
              ref={scrollContainerRef}
              className={cn(
                "flex items-center gap-0.5 overflow-x-auto scrollbar-none scroll-smooth px-1",
                isLargeList ? "w-full min-w-[280px]" : "max-w-fit"
              )}
            >
              {availableViews.map((def) => {
                const isActive = def.id === activeView
                return (
                  <button
                    key={def.id}
                    ref={isActive ? activeItemRef : null}
                    type="button"
                    onClick={() => setActiveView(def.id)}
                    className={cn(
                      "flex items-center gap-2 rounded-full px-3.5 py-1 text-[11px] font-bold transition-all duration-500 flex-shrink-0 whitespace-nowrap active:scale-[0.96] group relative",
                      isActive
                        ? "bg-background text-foreground shadow-sm ring-1 ring-black/5 dark:ring-white/5"
                        : "text-muted-foreground/40 hover:text-foreground/80 hover:bg-background/40"
                    )}
                  >
                    <div className="relative flex items-center justify-center">
                      <div
                        className={cn(
                          "h-1 w-1 rounded-full transition-all duration-500",
                          isActive ? "scale-100 opacity-100" : "scale-0 opacity-0 group-hover:scale-100 group-hover:opacity-60"
                        )}
                        style={{
                          backgroundColor: def.color,
                          boxShadow: isActive ? `0 0 8px ${def.color}66` : 'none'
                        }}
                      />
                    </div>

                    <ViewIcon
                      name={def.icon}
                      label={def.label}
                      className={cn("h-3.5 w-3.5 transition-all duration-500", isActive ? "scale-110" : "group-hover:scale-110")}
                      style={{ color: isActive ? def.color : "currentColor" }}
                    />

                    <span>{def.label}</span>
                  </button>
                )
              })}
            </div>
            {/* Edge shadows for scroll indication */}
            <div className="absolute left-1 top-1 bottom-1 w-4 bg-gradient-to-r from-background/30 to-transparent pointer-events-none rounded-l-full opacity-0 group-hover:opacity-100 transition-opacity" />
            <div className="absolute right-1 top-1 bottom-1 w-4 bg-gradient-to-l from-background/30 to-transparent pointer-events-none rounded-r-full opacity-0 group-hover:opacity-100 transition-opacity" />
          </div>

          {/* MOBILE: Slim Toggle */}
          <div className="md:hidden">
            <Sheet>
              <SheetTrigger asChild>
                <button
                  className="flex items-center gap-2 rounded-xl px-3 py-1 border bg-card/60 shadow-sm active:scale-95 transition-all text-[11px] font-bold"
                  style={{ borderColor: `${activeViewDef.color}33`, color: activeViewDef.color }}
                >
                  <ViewIcon name={activeViewDef.icon} label={activeViewDef.label} className="h-3.5 w-3.5" />
                  <span className="text-foreground">{activeViewDef.label}</span>
                  <ChevronDown className="h-3 w-3 text-muted-foreground/50" />
                </button>
              </SheetTrigger>
              <SheetContent side="bottom" className="rounded-t-[40px] p-6 pb-12 border-t-0 bg-card/98 backdrop-blur-2xl">
                <div className="w-12 h-1.5 bg-muted/30 rounded-full mx-auto mb-8" />
                <SheetHeader className="mb-8 text-center sm:text-left pr-12 sm:pr-0">
                  <SheetTitle className="text-2xl font-black leading-tight">
                    {availableViews.length} Available Views
                  </SheetTitle>
                  <SheetDescription className="text-base font-medium">Switch your access context below</SheetDescription>
                </SheetHeader>
                <div className="grid gap-4 sm:grid-cols-2">
                  {availableViews.map((def) => {
                    const isActive = def.id === activeView
                    return (
                      <button
                        key={def.id}
                        onClick={() => setActiveView(def.id)}
                        className={cn(
                          "flex items-center gap-5 p-5 rounded-[24px] border transition-all duration-300 text-left group overflow-hidden",
                          isActive
                            ? "bg-card shadow-xl ring-1 ring-foreground/5 dark:ring-white/10"
                            : "hover:bg-muted/40 bg-muted/20"
                        )}
                        style={{ borderColor: isActive ? def.color : "transparent" }}
                      >
                        <div
                          className="p-3.5 rounded-2xl shrink-0 transition-transform duration-500 group-active:scale-90 shadow-sm"
                          style={{ backgroundColor: `${def.color}${isActive ? '22' : '11'}`, color: def.color }}
                        >
                          <ViewIcon name={def.icon} label={def.label} className="h-6 w-6" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <div className="flex items-center justify-between gap-2 mb-0.5">
                            <p className="font-bold text-base leading-none">{def.label}</p>
                            {isActive && <Check className="h-4 w-4 stroke-[3]" style={{ color: def.color }} />}
                          </div>
                          <p className="text-xs text-muted-foreground/80 font-medium line-clamp-1">{def.description}</p>
                        </div>
                      </button>
                    )
                  })}
                </div>
              </SheetContent>
            </Sheet>
          </div>
        </div>

        {/* RIGHT: Context Description (Slim) */}
        <div className="hidden xl:flex items-center shrink-0 pl-6 border-l border-border/20 gap-3">
          <p className="text-[11px] font-medium text-muted-foreground/60 max-w-[450px] truncate" title={activeViewDef.description}>
            {activeViewDef.description}
          </p>
        </div>
      </div>
    </div>
  )
}
