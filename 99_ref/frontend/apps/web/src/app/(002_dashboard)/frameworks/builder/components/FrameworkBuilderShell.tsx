"use client"

import { Activity, History, PlusCircle, Sparkles } from "lucide-react"
import {
  Button,
  Sheet,
  SheetContent,
  SheetHeader,
  SheetTitle,
  SheetTrigger,
  cn,
} from "@kcontrol/ui"
import { useRouter } from "next/navigation"
import { useBuilder } from "../hooks/useBuilder"
import { BuilderSidebar } from "./BuilderSidebar"
import { BuilderActivityPanel } from "./BuilderActivityPanel"
import { BuilderForm } from "./BuilderForm"
import { BuilderWorkbench } from "./BuilderWorkbench"
import { BuilderEnhanceTab } from "./BuilderEnhanceTab"
import { BuilderGapTab } from "./BuilderGapTab"

export function FrameworkBuilderShell({ embedded = false }: { embedded?: boolean }) {
  const b = useBuilder()
  const router = useRouter()

  const isStreamingOrCreating = b.isStreaming
    || b.phase === "creating"
    || b.phase === "enhance_applying"
    || b.phase === "phase1_streaming"
    || b.phase === "phase2_streaming"

  const failedApplyEvents = b.feedEvents
    .filter((ev) => ev.event === "change_failed")
    .map((ev: any) => ({
      entity_code: typeof ev.entity_code === "string" ? ev.entity_code : "item",
      change_type: typeof ev.change_type === "string" ? ev.change_type : "change",
      error: typeof ev.error === "string" ? ev.error : "Unknown error",
    }))

  return (
    <div
      className={cn(
        "flex overflow-hidden bg-background",
        embedded
          ? "h-[calc(100svh-240px)] min-h-[720px] rounded-2xl border border-border/60 shadow-sm"
          : "-m-4 h-[calc(100svh-56px)] md:-m-6 lg:-m-8",
      )}
    >
      <BuilderSidebar
        sessions={b.sessions}
        activeSessionId={b.activeSessionId}
        onSessionSelect={b.hydrateFromSession}
        onNewSession={b.resetBuildState}
        className="hidden w-72 shrink-0 border-r border-border/40 2xl:flex"
      />

      <main className="relative flex min-w-0 flex-1 flex-col bg-background/50">
        <header className="sticky top-0 z-40 flex h-14 shrink-0 items-center justify-between border-b border-border/40 bg-background/80 px-3 backdrop-blur-3xl sm:px-4 md:px-6">
          <div className="flex min-w-0 items-center gap-2 sm:gap-3">
            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="h-9 w-9 shrink-0 rounded-xl border border-border/40 2xl:hidden">
                  <History className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="left" className="w-72 border-r-border/40 bg-background/95 p-0 backdrop-blur-xl">
                <SheetHeader className="sr-only">
                  <SheetTitle>Recent Sessions</SheetTitle>
                </SheetHeader>
                <BuilderSidebar
                  sessions={b.sessions}
                  activeSessionId={b.activeSessionId}
                  onSessionSelect={b.hydrateFromSession}
                  onNewSession={b.resetBuildState}
                  className="h-full border-none pt-20"
                />
              </SheetContent>
            </Sheet>

            <nav className="flex shrink-0 items-center gap-0.5 rounded-xl border border-border/40 bg-muted/20 p-0.5 shadow-inner ring-1 ring-white/5">
              {[
                { id: "build", label: "Build Suite", shortLabel: "Build", icon: PlusCircle },
                { id: "enhance", label: "Framework Evolution", shortLabel: "Evolve", icon: Sparkles },
                { id: "gap", label: "Engine Coverage", shortLabel: "Coverage", icon: Activity },
              ].map((tab) => (
                <button
                  key={tab.id}
                  onClick={() => b.setActiveTab(tab.id as any)}
                  className={cn(
                    "group relative flex items-center gap-1.5 whitespace-nowrap rounded-lg px-2 py-1.5 text-[8px] font-black uppercase tracking-[0.08em] transition-all sm:rounded-xl sm:px-2.5 sm:text-[9px] sm:tracking-[0.1em] md:px-3",
                    b.activeTab === tab.id
                      ? "bg-background text-primary shadow-lg shadow-black/20 ring-1 ring-white/10"
                      : "text-muted-foreground/40 hover:bg-white/5 hover:text-muted-foreground/80",
                  )}
                >
                  {b.activeTab === tab.id && (
                    <div className="absolute inset-0 rounded-lg bg-primary/5 opacity-20 blur-md sm:rounded-xl" />
                  )}
                  <tab.icon className={cn("h-3 w-3 shrink-0", b.activeTab === tab.id ? "text-primary" : "opacity-40")} />
                  <span className="hidden sm:inline 2xl:hidden">{tab.shortLabel}</span>
                  <span className="hidden 2xl:inline">{tab.label}</span>
                </button>
              ))}
            </nav>
          </div>

          <div className="flex shrink-0 items-center gap-2 sm:gap-3">
            <div className="hidden items-center gap-2 rounded-2xl border border-border/40 bg-muted/10 px-3 py-1.5 ring-1 ring-white/5 md:flex lg:px-4">
              <div className={cn("h-1.5 w-1.5 rounded-full", isStreamingOrCreating ? "bg-primary animate-pulse shadow-[0_0_12px_rgba(var(--primary-rgb),0.6)]" : "bg-muted-foreground/20")} />
              <span className="hidden text-[9px] font-black uppercase tracking-widest text-muted-foreground/60 lg:inline">
                {isStreamingOrCreating ? "Syncing Logic" : "Standby"}
              </span>
            </div>

            <Sheet>
              <SheetTrigger asChild>
                <Button variant="ghost" size="icon" className="relative h-9 w-9 rounded-xl border border-border/40 xl:hidden">
                  {isStreamingOrCreating && <span className="absolute right-1.5 top-1.5 h-1.5 w-1.5 animate-ping rounded-full bg-primary" />}
                  <Activity className="h-4 w-4" />
                </Button>
              </SheetTrigger>
              <SheetContent side="right" className="w-80 border-l-border/40 bg-background/95 p-0 backdrop-blur-xl">
                <SheetHeader className="sr-only">
                  <SheetTitle>Build Activity</SheetTitle>
                </SheetHeader>
                <BuilderActivityPanel
                  phase={b.phase}
                  feedEvents={b.feedEvents}
                  isStreaming={b.isStreaming}
                  resultFrameworkId={b.resultFrameworkId}
                  onLaunchFramework={(id) => router.push(`/frameworks/${id}`)}
                  className="h-full border-none pt-20"
                />
              </SheetContent>
            </Sheet>
          </div>
        </header>

        <div className="flex-1 overflow-y-auto custom-scrollbar">
          <div className="h-full w-full">
            {b.activeTab === "build" && (
              <div className="h-full">
                {b.phase === "idle" || (b.phase === "failed" && b.hierarchyNodes.length === 0) ? (
                  <BuilderForm
                    frameworkName={b.frameworkName}
                    setFrameworkName={b.setFrameworkName}
                    frameworkType={b.frameworkType}
                    setFrameworkType={b.setFrameworkType}
                    categoryCode={b.categoryCode}
                    setCategoryCode={b.setCategoryCode}
                    userContext={b.userContext}
                    setUserContext={b.setUserContext}
                    uploadedFiles={b.uploadedFiles}
                    onFileDrop={b.setUploadedFiles}
                    onRemoveFile={(i) => b.setUploadedFiles((prev) => prev.filter((_, idx) => idx !== i))}
                    onPropose={b.handleProposeStructure}
                    isStreaming={b.isStreaming}
                    dragOver={b.dragOver}
                    setDragOver={b.setDragOver}
                  />
                ) : (
                  <BuilderWorkbench
                    phase={b.phase}
                    hierarchyNodes={b.hierarchyNodes}
                    selectedCode={b.selectedCode}
                    setSelectedCode={b.setSelectedCode}
                    nodeOverrides={b.nodeOverrides}
                    setNodeOverrides={b.setNodeOverrides}
                    isStreaming={b.isStreaming}
                    onGenerateControls={b.handleGenerateControls}
                    onCreateFramework={b.handleCreateFramework}
                    onReset={b.resetBuildState}
                    buildCreateApproved={b.buildCreateApproved}
                    setBuildCreateApproved={b.setBuildCreateApproved}
                    resultFrameworkId={b.resultFrameworkId}
                    onLaunchFramework={(id) => router.push(`/frameworks/${id}`)}
                    onEditNode={b.editNode}
                    onEditControl={b.editControl}
                    selectedItems={b.selectedItems}
                    onToggleItem={b.toggleItem}
                    className="h-full"
                  />
                )}
              </div>
            )}

            {b.activeTab === "enhance" && (
              <BuilderEnhanceTab
                phase={b.phase}
                isStreaming={b.isStreaming}
                availableFrameworks={b.availableFrameworks}
                enhanceFrameworkId={b.enhanceFrameworkId}
                setEnhanceFrameworkId={b.setEnhanceFrameworkId}
                enhanceContext={b.enhanceContext}
                setEnhanceContext={b.setEnhanceContext}
                loadingFrameworks={b.loadingFrameworks}
                onAnalyze={b.handleAnalyzeEnhance}
                proposals={b.proposals}
                onAcceptAll={b.acceptAllProposals}
                onRejectAll={b.rejectAllProposals}
                onToggleProposal={b.toggleProposal}
                onApply={b.handleApplyEnhancements}
                onCancelApply={b.handleCancelApply}
                enhanceApplyApproved={b.enhanceApplyApproved}
                setEnhanceApplyApproved={b.setEnhanceApplyApproved}
                enhanceAppliedCount={b.enhanceAppliedCount}
                enhanceApplyStats={b.enhanceApplyStats}
                resultFrameworkId={b.resultFrameworkId}
                onLaunchFramework={(id) => router.push(`/frameworks/${id}`)}
                failedApplyEvents={failedApplyEvents}
                enhanceUserContext={b.enhanceUserContext}
                setEnhanceUserContext={b.setEnhanceUserContext}
                enhanceUploadedFiles={b.enhanceUploadedFiles}
                setEnhanceUploadedFiles={b.setEnhanceUploadedFiles}
                enhanceDragOver={b.enhanceDragOver}
                setEnhanceDragOver={b.setEnhanceDragOver}
                enhanceUploading={b.enhanceUploading}
              />
            )}

            {b.activeTab === "gap" && (
              <BuilderGapTab
                availableFrameworks={b.availableFrameworks}
                gapFrameworkId={b.gapFrameworkId}
                setGapFrameworkId={b.setGapFrameworkId}
                loadingFrameworks={b.loadingFrameworks}
                onRunGapAnalysis={b.handleRunGapAnalysis}
                gapPolling={b.gapPolling}
                gapReport={b.gapReport}
                gapUserContext={b.gapUserContext}
                setGapUserContext={b.setGapUserContext}
                gapUploadedFiles={b.gapUploadedFiles}
                setGapUploadedFiles={b.setGapUploadedFiles}
                gapDragOver={b.gapDragOver}
                setGapDragOver={b.setGapDragOver}
                gapUploading={b.gapUploading}
              />
            )}
          </div>
        </div>
      </main>

      <BuilderActivityPanel
        phase={b.phase}
        feedEvents={b.feedEvents}
        isStreaming={b.isStreaming}
        resultFrameworkId={b.resultFrameworkId}
        onLaunchFramework={(id) => router.push(`/frameworks/${id}`)}
        className="hidden shrink-0 border-l border-border/40 xl:flex xl:w-72 2xl:w-80"
      />
    </div>
  )
}
