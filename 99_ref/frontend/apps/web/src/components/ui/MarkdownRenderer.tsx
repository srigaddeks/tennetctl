"use client"

import React from "react"
import ReactMarkdown from "react-markdown"
import remarkGfm from "remark-gfm"
import rehypeHighlight from "rehype-highlight"

/** Extract {#custom-id} from heading children OR auto-slug from text content. */
function headingMeta(children: React.ReactNode): { id: string; clean: React.ReactNode } {
  // Collect raw text
  const rawText = (function collect(node: React.ReactNode): string {
    if (typeof node === "string") return node
    if (Array.isArray(node)) return node.map(collect).join("")
    if (node && typeof node === "object" && "props" in (node as object))
      return collect((node as React.ReactElement<any>).props.children)
    return ""
  })(children)

  // Check for {#explicit-id} pattern
  const match = rawText.match(/\{#([^}]+)\}/)
  if (match) {
    const id = match[1].trim()
    // Strip the {#id} from children for display
    const strip = (node: React.ReactNode): React.ReactNode => {
      if (typeof node === "string") return node.replace(/\s*\{#[^}]+\}/g, "")
      if (Array.isArray(node)) return node.map(strip)
      if (node && typeof node === "object" && "props" in (node as object)) {
        const el = node as React.ReactElement<any>
        return { ...el, props: { ...el.props, children: strip(el.props.children) } }
      }
      return node
    }
    return { id, clean: strip(children) }
  }

  // Fallback: slugify from text content
  const id = rawText.toLowerCase().replace(/[^a-z0-9]+/g, "-").replace(/^-|-$/g, "")
  return { id, clean: children }
}

const DEFAULT_MD_COMPONENTS = {
  // ── Table family ──────────────────────────────────────────────────────────
  table({ children }: { children?: React.ReactNode }) {
    return (
      <div className="overflow-x-auto my-6 rounded-lg border border-border">
        <table className="w-full border-collapse text-sm">{children}</table>
      </div>
    )
  },
  thead({ children }: { children?: React.ReactNode }) {
    return <thead className="bg-muted/50">{children}</thead>
  },
  tbody({ children }: { children?: React.ReactNode }) {
    return <tbody>{children}</tbody>
  },
  tr({ children, ...props }: { children?: React.ReactNode; [k: string]: any }) {
    return (
      <tr
        className="border-b border-border transition-colors hover:bg-muted/50"
        {...props}
      >{children}</tr>
    )
  },
  th({ children }: { children?: React.ReactNode }) {
    return (
      <th className="px-4 py-3 text-left font-semibold text-[0.72rem] uppercase tracking-wider text-muted-foreground border-b-2 border-border border-r border-border/50 whitespace-nowrap">
        {children}
      </th>
    )
  },
  td({ children }: { children?: React.ReactNode }) {
    return (
      <td className="px-4 py-2.5 text-[0.87rem] text-foreground/90 border-r border-border/50 align-top leading-relaxed">
        {children}
      </td>
    )
  },
  // ── Blockquote ────────────────────────────────────────────────────────────
  blockquote({ children }: { children?: React.ReactNode }) {
    return (
      <blockquote className="border-l-4 border-muted-foreground/30 bg-muted/30 px-4 py-3 my-4 rounded-r-lg italic text-muted-foreground">
        {children}
      </blockquote>
    )
  },
  // ── Headings with anchor IDs ──────────────────────────────────────────────
  h1({ children }: { children?: React.ReactNode }) {
    const { id, clean } = headingMeta(children)
    return (
      <h1 id={id} className="text-2xl font-bold tracking-tight text-foreground border-b border-border pb-2 mb-6 mt-0 scroll-mt-16">
        {clean}
      </h1>
    )
  },
  h2({ children }: { children?: React.ReactNode }) {
    const { id, clean } = headingMeta(children)
    return (
      <h2 id={id} className="text-[1.15rem] font-bold tracking-tight text-foreground/95 border-b border-border/50 pb-1.5 mt-9 mb-3 scroll-mt-16">
        {clean}
      </h2>
    )
  },
  h3({ children }: { children?: React.ReactNode }) {
    const { id, clean } = headingMeta(children)
    return (
      <h3 id={id} className="text-base font-bold text-foreground/90 mt-7 mb-2 scroll-mt-16">
        {clean}
      </h3>
    )
  },
  h4({ children }: { children?: React.ReactNode }) {
    const { id, clean } = headingMeta(children)
    return (
      <h4 id={id} className="text-[0.85rem] font-semibold tracking-wider uppercase text-muted-foreground mt-6 mb-2 scroll-mt-16">
        {clean}
      </h4>
    )
  },
  // ── Inline ────────────────────────────────────────────────────────────────
  a({ href, children }: { href?: string; children?: React.ReactNode }) {
    const isAnchor = href?.startsWith("#")
    if (isAnchor) {
      return (
        <a
          href={href}
          onClick={e => {
            e.preventDefault()
            const target = document.getElementById(href!.slice(1))
            if (target) target.scrollIntoView({ behavior: "smooth", block: "start" })
          }}
          className="text-violet-600 hover:text-violet-700 dark:text-violet-400 dark:hover:text-violet-300 underline underline-offset-2 cursor-pointer"
        >{children}</a>
      )
    }
    return (
      <a href={href} target="_blank" rel="noopener noreferrer"
        className="text-violet-600 hover:text-violet-700 dark:text-violet-400 dark:hover:text-violet-300 underline underline-offset-2"
      >{children}</a>
    )
  },
  strong({ children }: { children?: React.ReactNode }) {
    return <strong className="font-bold text-foreground">{children}</strong>
  },
  p({ children }: { children?: React.ReactNode }) {
    return <p className="my-2.5 leading-relaxed text-foreground/80">{children}</p>
  },
  ul({ children }: { children?: React.ReactNode }) {
    return <ul className="list-disc list-outside my-3 space-y-1.5 text-foreground/80 ml-5">{children}</ul>
  },
  ol({ children }: { children?: React.ReactNode }) {
    return <ol className="list-decimal list-outside my-3 space-y-1.5 text-foreground/80 ml-5">{children}</ol>
  },
  li({ children }: { children?: React.ReactNode }) {
    return <li className="my-1.5 leading-relaxed text-foreground/80">{children}</li>
  },
  hr() {
    return <hr className="border-border my-7" />
  },
  code({ children, className }: { children?: React.ReactNode; className?: string }) {
    const isBlock = className?.includes("language-")
    if (isBlock) return <code className={className}>{children}</code>
    return (
      <code className="font-mono text-[0.8rem] text-violet-700 dark:text-violet-300 bg-violet-100 dark:bg-violet-900/30 px-1.5 py-0.5 rounded">
        {children}
      </code>
    )
  },
}

export function MarkdownRenderer({
  content,
  className
}: {
  content: string;
  className?: string;
}) {
  return (
    <div className={`report-md prose prose-sm dark:prose-invert max-w-none ${className ?? ""}`}>
      <ReactMarkdown
        remarkPlugins={[remarkGfm]}
        rehypePlugins={[rehypeHighlight]}
        components={DEFAULT_MD_COMPONENTS}
      >
        {content}
      </ReactMarkdown>
    </div>
  )
}
