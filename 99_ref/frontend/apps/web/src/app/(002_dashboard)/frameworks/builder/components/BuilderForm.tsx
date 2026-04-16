"use client"

import {
  FileText,
  Upload,
  X,
  Sparkles,
  ChevronRight,
  ArrowRight,
  PlusCircle,
  Activity,
  Loader2,
} from "lucide-react"
import {
  Button,
  Input,
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
  cn,
} from "@kcontrol/ui"

interface BuilderFormProps {
  frameworkName: string
  setFrameworkName: (val: string) => void
  frameworkType: string
  setFrameworkType: (val: string) => void
  categoryCode: string
  setCategoryCode: (val: string) => void
  userContext: string
  setUserContext: (val: string) => void
  uploadedFiles: File[]
  onFileDrop: (files: File[] | ((prev: File[]) => File[])) => void
  onRemoveFile: (index: number) => void
  onPropose: () => void
  isStreaming: boolean
  dragOver: boolean
  setDragOver: (over: boolean) => void
  className?: string
}

export function BuilderForm({
  frameworkName,
  setFrameworkName,
  frameworkType,
  setFrameworkType,
  categoryCode,
  setCategoryCode,
  userContext,
  setUserContext,
  uploadedFiles,
  onFileDrop,
  onRemoveFile,
  onPropose,
  isStreaming,
  dragOver,
  setDragOver,
  className,
}: BuilderFormProps) {
  return (
    <div className={cn("max-w-5xl mx-auto py-6 md:py-10 px-4 md:px-8 space-y-6 md:space-y-10 animate-in fade-in slide-in-from-bottom-8 duration-1000", className)}>
      <header className="space-y-2 text-center md:text-left">
        <div className="flex items-center justify-center md:justify-start gap-2 mb-1">
          <div className="h-8 w-8 rounded-xl bg-primary/10 flex items-center justify-center border border-primary/20 shadow-inner group">
            <Sparkles className="h-4 w-4 text-primary group-hover:scale-110 transition-transform" />
          </div>
          <span className="text-[10px] font-black uppercase tracking-[0.3em] text-primary/60">Architectural Suite</span>
        </div>
        <h1 className="text-xl md:text-2xl lg:text-3xl font-bold bg-gradient-to-br from-foreground via-foreground to-muted-foreground bg-clip-text text-transparent tracking-tight leading-tight">Design Your Security Framework</h1>
        <p className="text-xs md:text-sm text-muted-foreground/60 max-w-2xl font-medium leading-relaxed">Upload documents and state your goals. Our AI will propose a customized requirement hierarchy.</p>
      </header>

      <div className="rounded-2xl md:rounded-[32px] lg:rounded-[40px] border border-border/60 bg-card/10 backdrop-blur-sm shadow-2xl relative overflow-hidden ring-1 ring-white/[0.08]">
        <div className="grid grid-cols-1 xl:grid-cols-2 divide-y xl:divide-y-0 xl:divide-x divide-border/40">
          {/* Identity Section */}
          <section className="p-5 md:p-8 lg:p-10 space-y-5 md:space-y-8">
            <div className="space-y-5 relative z-10">
              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/80 ml-1">Framework Identity</label>
                <Input
                  placeholder="e.g. NIST 800-53 R5 / Internal Corporate Policy"
                  className="min-h-[44px] py-2.5 rounded-xl border-border/60 bg-background/50 px-5 text-sm font-medium placeholder:text-muted-foreground/60 focus:ring-4 focus:ring-primary/5 transition-all shadow-inner focus:border-primary/40"
                  value={frameworkName}
                  onChange={e => setFrameworkName(e.target.value)}
                />
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 md:gap-6">
                <div className="space-y-2 flex flex-col">
                  <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/80 ml-1">Archetype</label>
                  <Select value={frameworkType} onValueChange={setFrameworkType}>
                    <SelectTrigger className="w-full min-h-[44px] py-2 rounded-xl border border-border/60 bg-background/50 px-4 md:px-5 text-sm font-medium focus:ring-4 focus:ring-primary/5 transition-all shadow-inner focus:border-primary/40 text-left h-auto">
                      <SelectValue placeholder="Archetype" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="it_cyber">IT/Cyber Audit</SelectItem>
                      <SelectItem value="regulatory">Regulatory Audit</SelectItem>
                      <SelectItem value="process">Process Audit</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
                <div className="space-y-2 flex flex-col">
                  <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/80 ml-1">Sub-Sector</label>
                  <Select value={categoryCode} onValueChange={setCategoryCode}>
                    <SelectTrigger className="w-full min-h-[44px] py-2 rounded-xl border border-border/60 bg-background/50 px-4 md:px-5 text-sm font-medium focus:ring-4 focus:ring-primary/5 transition-all shadow-inner focus:border-primary/40 text-left h-auto">
                      <SelectValue placeholder="Sector" />
                    </SelectTrigger>
                    <SelectContent>
                      <SelectItem value="security">Security & Comms</SelectItem>
                      <SelectItem value="privacy">Global Privacy</SelectItem>
                      <SelectItem value="legal">Regulatory Law</SelectItem>
                    </SelectContent>
                  </Select>
                </div>
              </div>

              <div className="space-y-2">
                <label className="text-[10px] font-black uppercase tracking-[0.2em] text-muted-foreground/80 ml-1">Strategic Intent & Scope</label>
                <textarea
                  placeholder="Describe your goals and compliance requirements..."
                  className="w-full min-h-[160px] md:min-h-[200px] rounded-2xl border border-border/60 bg-background/50 px-5 py-5 text-sm font-medium placeholder:text-muted-foreground/60 focus:ring-4 focus:ring-primary/5 transition-all resize-none shadow-inner focus:border-primary/40 leading-relaxed text-foreground/90 scrollbar-none"
                  value={userContext}
                  onChange={e => setUserContext(e.target.value)}
                />
              </div>
            </div>
          </section>

          {/* Upload & Action Section */}
          <section className="flex flex-col h-full">
            <div
              onDragOver={e => { e.preventDefault(); setDragOver(true); }}
              onDragLeave={() => setDragOver(false)}
              onDrop={e => {
                e.preventDefault();
                setDragOver(false);
                onFileDrop(prev => [...prev, ...Array.from(e.dataTransfer.files)]);
              }}
              className={cn(
                "flex-1 flex flex-col items-center justify-center p-5 md:p-8 lg:p-10 transition-all duration-700 relative overflow-hidden group/drop",
                dragOver ? "bg-primary/5 scale-[0.98]" : "bg-primary/[0.02] hover:bg-primary/[0.04]",
                uploadedFiles.length > 0 ? "bg-emerald-500/[0.02]" : ""
              )}
            >
              {uploadedFiles.length === 0 ? (
                <div className="text-center space-y-4 relative z-10 transition-transform group-hover/drop:scale-105 duration-700">
                  <div className="h-14 w-14 md:h-16 md:w-16 rounded-[20px] md:rounded-[24px] bg-primary/10 flex items-center justify-center mx-auto border border-primary/20 shadow-lg animate-bounce-suble">
                    <Upload className="h-6 w-6 md:h-7 md:w-7 text-primary" />
                  </div>
                  <div className="space-y-1">
                    <h3 className="text-sm md:text-base font-bold text-foreground/90">Knowledge Base</h3>
                    <p className="text-[10px] text-muted-foreground/50 font-medium max-w-[200px] mx-auto leading-tight">Drop documents to train the AI on your context</p>
                  </div>
                  <Button variant="outline" size="sm" className="h-9 px-6 text-[10px] font-black uppercase tracking-[0.2em] rounded-xl border-primary/20 hover:bg-primary/10 transition-all shadow-xl shadow-primary/5" asChild>
                    <label className="cursor-pointer">
                      Inspect Local Files
                      <input
                        type="file"
                        multiple
                        className="hidden"
                        onChange={e => onFileDrop(prev => [...prev, ...Array.from(e.target.files || [])])}
                      />
                    </label>
                  </Button>
                </div>
              ) : (
                <div className="w-full space-y-4 relative z-10">
                  <div className="flex items-center justify-between px-2 mb-2">
                    <span className="text-[10px] font-black uppercase tracking-[0.2em] text-emerald-400">Inventory ({uploadedFiles.length})</span>
                    <button onClick={() => onFileDrop([])} className="text-[10px] font-black uppercase tracking-widest text-muted-foreground/40 hover:text-red-400 transition-colors">Wipe All</button>
                  </div>
                  <ul className="space-y-2 max-h-[180px] md:max-h-[220px] overflow-y-auto px-1 custom-scrollbar">
                    {uploadedFiles.map((file, i) => (
                      <li key={i} className="group/file flex items-center gap-3 rounded-2xl bg-background/40 border border-border/20 p-3 transition-all hover:bg-emerald-500/10 hover:border-emerald-500/40 shadow-sm">
                        <div className="h-8 w-8 rounded-xl bg-emerald-500/10 flex items-center justify-center border border-emerald-500/20 group-hover/file:scale-110 transition-transform">
                          <FileText className="h-4 w-4 text-emerald-400" />
                        </div>
                        <div className="flex-1 min-w-0">
                          <p className="text-[10px] font-bold text-foreground truncate">{file.name}</p>
                          <p className="text-[8px] font-black text-muted-foreground/40 uppercase tracking-tighter">{(file.size / 1024).toFixed(0)} KB</p>
                        </div>
                        <button
                          onClick={() => onRemoveFile(i)}
                          className="h-7 w-7 flex items-center justify-center rounded-lg hover:bg-red-500/20 text-muted-foreground/30 hover:text-red-400 transition-all opacity-0 group-hover/file:opacity-100"
                        >
                          <X className="h-3 w-3" />
                        </button>
                      </li>
                    ))}
                  </ul>
                  <Button variant="ghost" className="w-full h-10 border border-dashed border-emerald-500/20 rounded-2xl text-[10px] font-black uppercase tracking-[0.2em] text-emerald-500/40 hover:text-emerald-500 hover:bg-emerald-500/5 transition-all" asChild>
                    <label className="cursor-pointer">
                      <PlusCircle className="h-3.5 w-3.5 mr-2" /> Append More
                      <input type="file" multiple className="hidden" onChange={e => onFileDrop(prev => [...prev, ...Array.from(e.target.files || [])])} />
                    </label>
                  </Button>
                </div>
              )}
            </div>

            <div className="p-5 md:p-8 lg:p-10 bg-primary/5 border-t border-border/20 relative overflow-hidden group/callout mt-auto">
              <div className="space-y-4 relative z-10">
                <div className="flex flex-col gap-1">
                  <h4 className="text-[10px] font-black uppercase tracking-[0.2em] text-primary/80">Build</h4>
                  <p className="text-[11px] font-medium text-muted-foreground/60 leading-relaxed">AI will generate the full framework — requirements, controls, risks, and mappings.</p>
                </div>
                <Button
                  size="lg"
                  className="w-full min-h-[44px] md:min-h-[48px] rounded-xl text-[10px] md:text-xs font-bold uppercase tracking-widest gap-2 md:gap-3 shadow-[0_20px_40px_-10px_rgba(var(--primary-rgb),0.3)] active:scale-[0.98] transition-all relative overflow-hidden group/btn h-auto px-4 py-2"
                  onClick={onPropose}
                  disabled={isStreaming}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/10 to-transparent -translate-x-full group-hover/btn:translate-x-full transition-transform duration-1000" />
                  {isStreaming ? (
                    <Loader2 className="h-4 w-4 animate-spin" />
                  ) : (
                    <Sparkles className="h-4 w-4" />
                  )}
                  {isStreaming ? "Building..." : "Build Framework"}
                  <ArrowRight className="h-4 w-4 ml-1 opacity-40 group-hover/btn:translate-x-1 transition-transform" />
                </Button>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  )
}
