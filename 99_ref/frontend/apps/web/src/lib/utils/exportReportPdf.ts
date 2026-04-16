/**
 * Professional PDF export for K-Control GRC Reports.
 *
 * Uses @react-pdf/renderer to produce a proper vector PDF suitable for
 * publishing as an audit report. Parses markdown into structured blocks,
 * renders with cover page, logo, page numbers, headers and footers.
 */

/* eslint-disable @typescript-eslint/no-explicit-any */

import React from "react"
import {
  Document,
  Page,
  Text as PdfText,
  View,
  Image as PdfImage,
  StyleSheet,
  pdf,
} from "@react-pdf/renderer"
// @react-pdf/renderer uses its own Style type — use any for style props
type Style = Record<string, any>
import { KREESALIS_LOGO_BASE64 } from "./kreesalisLogoBase64"

// ── Colours ───────────────────────────────────────────────────────────────────

const C = {
  brand: "#6366f1",
  coverBg: "#0f0f23",
  coverText: "#ffffff",
  h1: "#0f0f23",
  h2: "#1e1b4b",
  h3: "#312e81",
  body: "#1f2937",
  muted: "#6b7280",
  subtle: "#9ca3af",
  border: "#e5e7eb",
  codeBg: "#f3f4f6",
  tableTh: "#f0f0ff",
  tableAlt: "#fafafa",
  blockquote: "#f5f3ff",
  badgeBorder: "#c7d2fe",
  badgeBg: "#eef2ff",
} as const

// ── Styles ────────────────────────────────────────────────────────────────────

const S = StyleSheet.create({
  page: {
    fontFamily: "Helvetica",
    fontSize: 10,
    color: C.body,
    backgroundColor: "#ffffff",
    paddingTop: 54,
    paddingBottom: 52,
    paddingLeft: 52,
    paddingRight: 52,
  },
  coverPage: {
    fontFamily: "Helvetica",
    backgroundColor: C.coverBg,
    paddingTop: 64,
    paddingBottom: 60,
    paddingLeft: 60,
    paddingRight: 60,
    display: "flex",
    flexDirection: "column",
    justifyContent: "space-between",
    height: "100%",
  } as Style,
  coverTopStrip: {
    position: "absolute",
    top: 0, left: 0, right: 0,
    height: 4,
    backgroundColor: C.brand,
  },
  coverLogo: { width: 130, height: 40, objectFit: "contain", marginBottom: 32 } as Style,
  coverAccentBar: { width: 56, height: 4, backgroundColor: C.brand, borderRadius: 2, marginBottom: 20 },
  coverBadge: {
    alignSelf: "flex-start",
    backgroundColor: C.badgeBg,
    borderColor: C.badgeBorder,
    borderWidth: 1,
    borderRadius: 100,
    paddingHorizontal: 10,
    paddingVertical: 3,
    marginBottom: 16,
  },
  coverBadgeText: { fontSize: 7, fontFamily: "Helvetica-Bold", color: C.brand, letterSpacing: 1.2 } as Style,
  coverTitle: { fontSize: 26, fontFamily: "Helvetica-Bold", color: C.coverText, lineHeight: 1.25, marginBottom: 10 } as Style,
  coverSubtitle: { fontSize: 11, color: "#a5b4fc", letterSpacing: 1, marginBottom: 28 } as Style,
  coverDivider: { borderBottomWidth: 1, borderBottomColor: "#3730a3", marginBottom: 22 },
  coverMetaRow: { flexDirection: "row", alignItems: "center", gap: 6, marginBottom: 5 } as Style,
  coverMetaLabel: { fontSize: 8, color: "#818cf8", fontFamily: "Helvetica-Bold", width: 90 } as Style,
  coverMetaValue: { fontSize: 9, color: "#e0e7ff" } as Style,
  coverFooterRow: { flexDirection: "row", justifyContent: "space-between", alignItems: "flex-end" } as Style,
  coverFooterText: { fontSize: 7.5, color: "#6b7280" } as Style,
  coverClassified: { fontSize: 7, color: "#a5b4fc", fontFamily: "Helvetica-Bold", letterSpacing: 1.5 } as Style,

  pageHeader: {
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    paddingBottom: 8,
    marginBottom: 16,
    borderBottomWidth: 1,
    borderBottomColor: C.border,
  } as Style,
  pageHeaderLogo: { width: 60, height: 18, objectFit: "contain" } as Style,
  pageHeaderTitle: { fontSize: 7, color: C.subtle },
  pageHeaderDate: { fontSize: 7, color: C.subtle },

  pageFooter: {
    position: "absolute",
    bottom: 24,
    left: 52,
    right: 52,
    flexDirection: "row",
    justifyContent: "space-between",
    alignItems: "center",
    borderTopWidth: 1,
    borderTopColor: C.border,
    paddingTop: 6,
  } as Style,
  pageFooterText: { fontSize: 7, color: C.subtle },
  pageFooterPage: { fontSize: 7, color: C.muted, fontFamily: "Helvetica-Bold" } as Style,

  h1: { fontSize: 16, fontFamily: "Helvetica-Bold", color: C.h1, marginTop: 20, marginBottom: 8 } as Style,
  h2: { fontSize: 12, fontFamily: "Helvetica-Bold", color: C.h2, marginTop: 18, marginBottom: 6, paddingBottom: 4, borderBottomWidth: 1, borderBottomColor: C.border } as Style,
  h3: { fontSize: 10.5, fontFamily: "Helvetica-Bold", color: C.h3, marginTop: 12, marginBottom: 4 } as Style,
  h4: { fontSize: 10, fontFamily: "Helvetica-Bold", color: C.body, marginTop: 8, marginBottom: 3 } as Style,
  p: { fontSize: 10, lineHeight: 1.65, marginBottom: 7, color: C.body } as Style,

  li: { flexDirection: "row", marginBottom: 3, paddingLeft: 4 } as Style,
  liBullet: { width: 14, fontSize: 10, color: C.brand, lineHeight: 1.65 } as Style,
  liNumber: { width: 18, fontSize: 10, color: C.brand, fontFamily: "Helvetica-Bold", lineHeight: 1.65 } as Style,
  liContent: { flex: 1, fontSize: 10, lineHeight: 1.65, color: C.body } as Style,

  listContainer: { marginBottom: 7 } as Style,

  inlineCode: { fontFamily: "Courier", fontSize: 8.5, backgroundColor: C.codeBg, borderRadius: 2 } as Style,
  codeBlock: {
    backgroundColor: C.codeBg,
    borderColor: C.border,
    borderWidth: 1,
    borderRadius: 5,
    padding: 10,
    marginVertical: 7,
    fontFamily: "Courier",
    fontSize: 8,
    lineHeight: 1.5,
    color: "#374151",
  } as Style,

  blockquote: {
    borderLeftWidth: 3,
    borderLeftColor: C.brand,
    backgroundColor: C.blockquote,
    paddingHorizontal: 12,
    paddingVertical: 6,
    marginVertical: 7,
    borderRadius: 3,
  },
  blockquoteText: { fontSize: 10, fontFamily: "Helvetica-Oblique", color: "#4b5563", lineHeight: 1.6 } as Style,

  table: { marginVertical: 8, borderColor: C.border, borderWidth: 0.5, borderRadius: 4 },
  tableRow: { flexDirection: "row", borderBottomWidth: 0.5, borderBottomColor: C.border } as Style,
  tableRowAlt: { backgroundColor: C.tableAlt },
  tableTh: {
    backgroundColor: C.tableTh,
    paddingVertical: 5,
    paddingHorizontal: 7,
    fontSize: 8.5,
    fontFamily: "Helvetica-Bold",
    color: C.h2,
    flex: 1,
    borderRightWidth: 0.5,
    borderRightColor: C.border,
  } as Style,
  tableTd: {
    paddingVertical: 4,
    paddingHorizontal: 7,
    fontSize: 8.5,
    color: C.body,
    flex: 1,
    borderRightWidth: 0.5,
    borderRightColor: C.border,
    lineHeight: 1.5,
  } as Style,

  hr: { borderBottomWidth: 1, borderBottomColor: C.border, marginVertical: 14 },
  confidentialityBox: {
    backgroundColor: "#fffbeb",
    borderColor: "#fbbf24",
    borderWidth: 1,
    borderRadius: 5,
    paddingHorizontal: 12,
    paddingVertical: 8,
    marginBottom: 16,
  },
  confidentialityText: { fontSize: 8.5, color: "#92400e", lineHeight: 1.5 } as Style,
})

// ── Markdown → block AST ─────────────────────────────────────────────────────

type Block =
  | { type: "h1" | "h2" | "h3" | "h4"; text: string }
  | { type: "p"; text: string }
  | { type: "ul"; items: string[] }
  | { type: "ol"; items: string[] }
  | { type: "code"; text: string }
  | { type: "blockquote"; text: string }
  | { type: "hr" }
  | { type: "table"; headers: string[]; rows: string[][] }

function parseMarkdownToBlocks(md: string): Block[] {
  const lines = md.split("\n")
  const blocks: Block[] = []
  let i = 0

  while (i < lines.length) {
    const line = lines[i].trimEnd()

    const hm = line.match(/^(#{1,4})\s+(.+)/)
    if (hm) {
      const level = hm[1].length as 1 | 2 | 3 | 4
      blocks.push({ type: `h${level}` as "h1" | "h2" | "h3" | "h4", text: hm[2].trim() })
      i++; continue
    }

    if (/^[-*_]{3,}$/.test(line.trim())) {
      blocks.push({ type: "hr" }); i++; continue
    }

    if (line.startsWith("```") || line.startsWith("~~~")) {
      const fence = line.slice(0, 3)
      const codeLines: string[] = []
      i++
      while (i < lines.length && !lines[i].startsWith(fence)) { codeLines.push(lines[i]); i++ }
      i++
      blocks.push({ type: "code", text: codeLines.join("\n") }); continue
    }

    if (line.startsWith("> ")) {
      const quoteLines: string[] = []
      while (i < lines.length && lines[i].startsWith("> ")) { quoteLines.push(lines[i].slice(2)); i++ }
      blocks.push({ type: "blockquote", text: quoteLines.join(" ") }); continue
    }

    if (line.includes("|") && i + 1 < lines.length && /^\s*\|?[-:| ]+\|?/.test(lines[i + 1])) {
      const parseRow = (r: string) => r.replace(/^\||\|$/g, "").split("|").map(c => c.trim())
      const headers = parseRow(line)
      i += 2
      const rows: string[][] = []
      while (i < lines.length && lines[i].trim().startsWith("|")) { rows.push(parseRow(lines[i])); i++ }
      blocks.push({ type: "table", headers, rows }); continue
    }

    if (/^[-*+] /.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^[-*+] /.test(lines[i].trimEnd())) {
        items.push(lines[i].replace(/^[-*+] /, "").trim()); i++
        while (i < lines.length && lines[i].startsWith("  ")) { items[items.length - 1] += " " + lines[i].trim(); i++ }
      }
      blocks.push({ type: "ul", items }); continue
    }

    if (/^\d+\. /.test(line)) {
      const items: string[] = []
      while (i < lines.length && /^\d+\. /.test(lines[i].trimEnd())) {
        items.push(lines[i].replace(/^\d+\. /, "").trim()); i++
        while (i < lines.length && lines[i].startsWith("  ")) { items[items.length - 1] += " " + lines[i].trim(); i++ }
      }
      blocks.push({ type: "ol", items }); continue
    }

    if (line.trim() === "") { i++; continue }

    const paraLines: string[] = []
    while (
      i < lines.length &&
      lines[i].trim() !== "" &&
      !lines[i].match(/^#{1,4} /) &&
      !lines[i].match(/^[-*+] /) &&
      !lines[i].match(/^\d+\. /) &&
      !lines[i].startsWith("> ") &&
      !lines[i].startsWith("```")
    ) {
      paraLines.push(lines[i].trim()); i++
    }
    if (paraLines.length) blocks.push({ type: "p", text: paraLines.join(" ") })
    else i++
  }

  return blocks
}

// ── Inline text renderer ─────────────────────────────────────────────────────

function renderInline(raw: string, style: Style): React.ReactElement {
  const parts: React.ReactElement[] = []
  const re = /(\*\*([^*]+)\*\*|\*([^*]+)\*|`([^`]+)`|([^*`]+))/g
  let match
  let n = 0
  while ((match = re.exec(raw)) !== null) {
    if (match[2]) {
      parts.push(React.createElement(PdfText, { key: n++, style: { ...style, fontFamily: "Helvetica-Bold" } as Style }, match[2]))
    } else if (match[3]) {
      parts.push(React.createElement(PdfText, { key: n++, style: { ...style, fontFamily: "Helvetica-Oblique" } as Style }, match[3]))
    } else if (match[4]) {
      parts.push(React.createElement(PdfText, { key: n++, style: { ...style, ...S.inlineCode } as Style }, match[4]))
    } else if (match[5]) {
      parts.push(React.createElement(PdfText, { key: n++, style }, match[5]))
    }
  }
  if (parts.length === 0) return React.createElement(PdfText, { style }, raw)
  return React.createElement(PdfText, { style }, ...parts)
}

// ── Block → PDF element ───────────────────────────────────────────────────────

function blockToElement(block: Block, idx: number): React.ReactElement | null {
  switch (block.type) {
    case "h1": return React.createElement(PdfText, { key: idx, style: S.h1 }, block.text)
    case "h2": return React.createElement(PdfText, { key: idx, style: S.h2 }, block.text)
    case "h3": return React.createElement(PdfText, { key: idx, style: S.h3 }, block.text)
    case "h4": return React.createElement(PdfText, { key: idx, style: S.h4 }, block.text)

    case "p":
      return React.createElement(View, { key: idx }, renderInline(block.text, S.p))

    case "ul":
      return React.createElement(
        View, { key: idx, style: S.listContainer },
        ...block.items.map((item, j) =>
          React.createElement(View, { key: j, style: S.li },
            React.createElement(PdfText, { style: S.liBullet }, "\u2022"),
            renderInline(item, S.liContent)
          )
        )
      )

    case "ol":
      return React.createElement(
        View, { key: idx, style: S.listContainer },
        ...block.items.map((item, j) =>
          React.createElement(View, { key: j, style: S.li },
            React.createElement(PdfText, { style: S.liNumber }, `${j + 1}.`),
            renderInline(item, S.liContent)
          )
        )
      )

    case "code":
      return React.createElement(PdfText, { key: idx, style: S.codeBlock }, block.text)

    case "blockquote":
      return React.createElement(
        View, { key: idx, style: S.blockquote },
        renderInline(block.text, S.blockquoteText)
      )

    case "hr":
      return React.createElement(View, { key: idx, style: S.hr })

    case "table":
      return React.createElement(
        View, { key: idx, style: S.table },
        React.createElement(
          View, { style: S.tableRow },
          ...block.headers.map((h, j) =>
            React.createElement(PdfText, { key: j, style: S.tableTh }, h)
          )
        ),
        ...block.rows.map((row, ri) =>
          React.createElement(
            View, { key: ri, style: ri % 2 === 1 ? [S.tableRow, S.tableRowAlt] : S.tableRow },
            ...row.map((cell, ci) =>
              React.createElement(PdfText, { key: ci, style: S.tableTd }, cell)
            )
          )
        )
      )

    default:
      return null
  }
}

// ── Document types ────────────────────────────────────────────────────────────

export interface PdfTemplateConfig {
  coverStyle: "dark_navy" | "light_minimal" | "gradient_accent"
  primaryColor: string
  secondaryColor: string
  headerText?: string
  footerText?: string
  preparedBy?: string
  docRefPrefix?: string
  classificationLabel?: string
}

export interface ReportPdfMeta {
  title: string
  reportType: string
  generatedAt?: string
  wordCount?: number
  orgName?: string
  workspaceName?: string
  confidential?: boolean
  template?: PdfTemplateConfig
}

// ── Document builder ──────────────────────────────────────────────────────────

function buildDocument(markdown: string, meta: ReportPdfMeta): React.ReactElement {
  const blocks = parseMarkdownToBlocks(markdown)
  const tmpl = meta.template

  // Resolve template-aware values (fall back to defaults)
  const primaryColor = tmpl?.primaryColor ?? "#1e2a45"
  const secondaryColor = tmpl?.secondaryColor ?? "#c9a96e"
  const coverStyle = tmpl?.coverStyle ?? "dark_navy"
  const isLightCover = coverStyle === "light_minimal"

  const coverBgColor = isLightCover ? "#ffffff" : (coverStyle === "gradient_accent" ? primaryColor : C.coverBg)
  const coverTextColor = isLightCover ? C.h1 : C.coverText
  const coverSubtitleColor = isLightCover ? C.muted : "#a5b4fc"
  const coverDividerColor = isLightCover ? C.border : "#3730a3"
  const coverMetaLabelColor = isLightCover ? C.muted : "#818cf8"
  const coverMetaValueColor = isLightCover ? C.body : "#e0e7ff"

  const reportTypeLabel = meta.reportType
    .replace(/_/g, " ")
    .replace(/\b\w/g, c => c.toUpperCase())

  const generatedStr = meta.generatedAt
    ? new Date(meta.generatedAt).toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })
    : new Date().toLocaleDateString("en-US", { year: "numeric", month: "long", day: "numeric" })

  const headerTitle = tmpl?.headerText
    ? (tmpl.headerText.length > 55 ? tmpl.headerText.slice(0, 52) + "…" : tmpl.headerText)
    : (meta.title.length > 55 ? meta.title.slice(0, 52) + "…" : meta.title)
  const isConfidential = meta.confidential !== false
  const classificationLabel = tmpl?.classificationLabel ?? (isConfidential ? "CONFIDENTIAL" : "INTERNAL")
  const footerLeft = tmpl?.footerText ?? `K-Control GRC Report · ${reportTypeLabel}`
  const footerRight = tmpl?.footerText ? "" : "© Kreesalis"
  const preparedBy = tmpl?.preparedBy ?? "Kreesalis Security Team"

  const metaRows: Array<[string, string]> = [
    ...(meta.orgName ? [["Organisation", meta.orgName] as [string, string]] : []),
    ...(meta.workspaceName ? [["Workspace", meta.workspaceName] as [string, string]] : []),
    ["Generated", generatedStr],
    ...(meta.wordCount ? [[`Word count`, meta.wordCount.toLocaleString()] as [string, string]] : []),
    ["Prepared By", preparedBy],
    ["Classification", classificationLabel],
  ]

  const dynamicCoverPage: Style = { ...S.coverPage, backgroundColor: coverBgColor }
  const dynamicTopStrip: Style = { ...S.coverTopStrip, backgroundColor: secondaryColor }
  const dynamicAccentBar: Style = { ...S.coverAccentBar, backgroundColor: secondaryColor }
  const dynamicBadgeText: Style = { ...S.coverBadgeText, color: primaryColor }
  const dynamicTitle: Style = { ...S.coverTitle, color: coverTextColor }
  const dynamicSubtitle: Style = { ...S.coverSubtitle, color: coverSubtitleColor }
  const dynamicDivider: Style = { ...S.coverDivider, borderBottomColor: coverDividerColor }
  const dynamicMetaLabel: Style = { ...S.coverMetaLabel, color: coverMetaLabelColor }
  const dynamicMetaValue: Style = { ...S.coverMetaValue, color: coverMetaValueColor }
  const dynamicClassified: Style = { ...S.coverClassified, color: coverStyle === "dark_navy" ? "#a5b4fc" : primaryColor }

  // Cover page
  const coverPage = React.createElement(
    Page,
    { size: "A4", style: dynamicCoverPage },
    // Top accent strip
    React.createElement(View, { style: dynamicTopStrip }),
    // Main wrapper
    React.createElement(
      View,
      { style: { flex: 1, justifyContent: "space-between" } as Style },
      // Top content
      React.createElement(
        View,
        {},
        React.createElement(PdfImage, { src: KREESALIS_LOGO_BASE64, style: S.coverLogo }),
        React.createElement(View, { style: dynamicAccentBar }),
        React.createElement(
          View, { style: S.coverBadge },
          React.createElement(PdfText, { style: dynamicBadgeText }, reportTypeLabel.toUpperCase())
        ),
        React.createElement(PdfText, { style: dynamicTitle }, meta.title),
        React.createElement(PdfText, { style: dynamicSubtitle }, "K-CONTROL GRC PLATFORM REPORT"),
        React.createElement(View, { style: dynamicDivider }),
        ...metaRows.map(([label, value], i) =>
          React.createElement(
            View, { key: i, style: S.coverMetaRow },
            React.createElement(PdfText, { style: dynamicMetaLabel }, label + ":"),
            React.createElement(PdfText, { style: dynamicMetaValue }, value)
          )
        )
      ),
      // Bottom footer
      React.createElement(
        View, { style: S.coverFooterRow },
        React.createElement(PdfText, { style: dynamicClassified },
          isConfidential ? `\u26D1 ${classificationLabel} \u2014 NOT FOR PUBLIC DISTRIBUTION` : classificationLabel
        ),
        React.createElement(PdfText, { style: S.coverFooterText }, "Powered by K-Control \u00B7 Kreesalis")
      )
    )
  )

  // Content pages
  const contentPage = React.createElement(
    Page,
    { size: "A4", style: S.page },

    // Running header (fixed)
    React.createElement(
      View, { style: S.pageHeader, fixed: true },
      React.createElement(PdfImage, { src: KREESALIS_LOGO_BASE64, style: S.pageHeaderLogo }),
      React.createElement(PdfText, { style: S.pageHeaderTitle }, headerTitle),
      React.createElement(PdfText, { style: S.pageHeaderDate }, generatedStr),
    ),

    // Confidentiality notice
    isConfidential
      ? React.createElement(
          View, { style: S.confidentialityBox },
          React.createElement(PdfText, { style: S.confidentialityText },
            "CONFIDENTIAL \u2014 This document contains proprietary and confidential information belonging to Kreesalis. " +
            "It is intended solely for the named recipient(s) and must not be copied, distributed, or disclosed " +
            "to any third party without prior written consent."
          )
        )
      : null,

    // Body blocks
    ...blocks.map((block, idx) => blockToElement(block, idx)),

    // Running footer (fixed)
    React.createElement(
      View, { style: S.pageFooter, fixed: true },
      React.createElement(PdfText, { style: S.pageFooterText }, footerLeft),
      React.createElement(PdfText, {
        style: S.pageFooterPage,
        render: ({ pageNumber, totalPages }: { pageNumber: number; totalPages: number }) =>
          `Page ${pageNumber} of ${totalPages}`,
      }),
      React.createElement(PdfText, { style: S.pageFooterText }, footerRight)
    )
  )

  return React.createElement(
    Document,
    {
      title: meta.title,
      author: "K-Control \u00B7 Kreesalis",
      subject: reportTypeLabel,
      creator: "K-Control GRC Platform",
      producer: "Kreesalis",
    },
    coverPage,
    contentPage
  )
}

// ── Public API ────────────────────────────────────────────────────────────────

/** Build the react-pdf Document element — used by both preview and download. */
export function buildReportDocument(markdown: string, meta: ReportPdfMeta): React.ReactElement {
  return buildDocument(markdown, meta)
}

/** Get a filename slug for the PDF. */
export function getReportPdfFilename(meta: ReportPdfMeta): string {
  const slug = meta.title.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "").slice(0, 50)
  return `kcontrol_${meta.reportType}_${slug}.pdf`
}

/** Generate blob and trigger a browser download. */
export async function exportReportToPdf(markdown: string, meta: ReportPdfMeta): Promise<void> {
  const doc = buildDocument(markdown, meta)
  const blob = await pdf(doc as any).toBlob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement("a")
  a.href = url
  a.download = getReportPdfFilename(meta)
  a.click()
  URL.revokeObjectURL(url)
}

/** Generate blob URL for preview (caller must revoke when done). */
export async function getReportPdfBlobUrl(markdown: string, meta: ReportPdfMeta): Promise<string> {
  const doc = buildDocument(markdown, meta)
  const blob = await pdf(doc as any).toBlob()
  return URL.createObjectURL(blob)
}
