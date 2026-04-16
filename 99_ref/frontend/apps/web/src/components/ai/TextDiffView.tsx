import { cn } from "@/lib/utils"

// ── Types ──────────────────────────────────────────────────────────────────────

interface TextDiffViewProps {
  original: string | string[]
  enhanced: string | string[]
  isArrayField?: boolean
  className?: string
}

type DiffOp = { type: "equal" | "insert" | "delete"; value: string }

// ── LCS Core ──────────────────────────────────────────────────────────────────

function lcs<T>(a: T[], b: T[], eq: (x: T, y: T) => boolean = (x, y) => x === y): DiffOp[] {
  const m = a.length
  const n = b.length

  // Space-optimised DP: two rows
  const dp: number[][] = Array.from({ length: m + 1 }, () => new Array<number>(n + 1).fill(0))
  for (let i = 1; i <= m; i++) {
    for (let j = 1; j <= n; j++) {
      dp[i][j] = eq(a[i - 1], b[j - 1])
        ? dp[i - 1][j - 1] + 1
        : Math.max(dp[i - 1][j], dp[i][j - 1])
    }
  }

  const ops: DiffOp[] = []
  let i = m, j = n
  while (i > 0 || j > 0) {
    if (i > 0 && j > 0 && eq(a[i - 1], b[j - 1])) {
      ops.unshift({ type: "equal", value: String(a[i - 1]) })
      i--; j--
    } else if (j > 0 && (i === 0 || dp[i][j - 1] >= dp[i - 1][j])) {
      ops.unshift({ type: "insert", value: String(b[j - 1]) })
      j--
    } else {
      ops.unshift({ type: "delete", value: String(a[i - 1]) })
      i--
    }
  }
  return ops
}

// ── Word-level diff (prose fields) ────────────────────────────────────────────
// Splits on word boundaries only (not whitespace tokens), so diff is cleaner
// and whitespace changes don't produce noisy highlights.

function computeWordDiff(original: string, enhanced: string): DiffOp[] {
  // Match words (including punctuation attached to them) and standalone whitespace runs
  // We include whitespace as non-diffable separators, not as diff tokens.
  const splitWords = (s: string) =>
    s.match(/\S+/g) ?? []

  const origWords = splitWords(original)
  const enhWords  = splitWords(enhanced)

  // Run LCS on word arrays
  const wordOps = lcs(origWords, enhWords)

  // Re-stitch: insert spaces between tokens to preserve readability.
  // Strategy: each token gets a leading space if the previous token was the
  // same type (same-span continuation). Between type transitions we emit an
  // explicit "equal" space span so the rendered output never concatenates words.
  const result: DiffOp[] = []
  for (let k = 0; k < wordOps.length; k++) {
    const op = wordOps[k]
    const prev = k > 0 ? wordOps[k - 1] : null

    if (prev === null) {
      // First token — no leading space
      result.push({ type: op.type, value: op.value })
    } else if (prev.type === op.type) {
      // Same type as previous — append space as part of this span
      result.push({ type: op.type, value: " " + op.value })
    } else {
      // Type changed — emit an explicit equal space first so spans never touch
      result.push({ type: "equal", value: " " })
      result.push({ type: op.type, value: op.value })
    }
  }
  return result
}

// ── Paragraph-level diff (long prose) ─────────────────────────────────────────
// When text has multiple paragraphs, diff at paragraph level first, then
// within changed paragraphs do word-level diff for precision.

function splitParagraphs(text: string): string[] {
  return text.split(/\n{2,}/).map(p => p.trim()).filter(Boolean)
}

interface ParagraphDiffBlock {
  type: "equal" | "replace" | "insert" | "delete"
  original?: string
  enhanced?: string
}

function computeParagraphDiff(original: string, enhanced: string): ParagraphDiffBlock[] {
  const origParas = splitParagraphs(original)
  const enhParas  = splitParagraphs(enhanced)

  // Use LCS on trimmed paragraphs
  const paraOps = lcs(origParas, enhParas, (a, b) => a === b)

  // Merge consecutive deletes+inserts into "replace" blocks for inline diff
  const blocks: ParagraphDiffBlock[] = []
  let k = 0
  while (k < paraOps.length) {
    const op = paraOps[k]
    if (op.type === "delete" && k + 1 < paraOps.length && paraOps[k + 1].type === "insert") {
      blocks.push({ type: "replace", original: op.value, enhanced: paraOps[k + 1].value })
      k += 2
    } else if (op.type === "equal") {
      blocks.push({ type: "equal", enhanced: op.value })
      k++
    } else if (op.type === "insert") {
      blocks.push({ type: "insert", enhanced: op.value })
      k++
    } else {
      blocks.push({ type: "delete", original: op.value })
      k++
    }
  }
  return blocks
}

// ── Line-level diff (array fields) ────────────────────────────────────────────

function computeLineDiff(origLines: string[], enhLines: string[]): DiffOp[] {
  return lcs(origLines, enhLines)
}

// ── Renderers ─────────────────────────────────────────────────────────────────

function InlineWordDiff({ original, enhanced }: { original: string; enhanced: string }) {
  const ops = computeWordDiff(original, enhanced)
  return (
    <span className="text-xs leading-relaxed whitespace-pre-wrap break-words">
      {ops.map((op, i) => {
        if (op.type === "equal") return <span key={i}>{op.value}</span>
        if (op.type === "delete") {
          return (
            <span key={i} className="bg-red-500/15 text-red-400 line-through decoration-red-400/60 rounded-sm px-0.5">
              {op.value}
            </span>
          )
        }
        return (
          <span key={i} className="bg-emerald-500/15 text-emerald-400 rounded-sm px-0.5">
            {op.value}
          </span>
        )
      })}
    </span>
  )
}

function ParagraphDiffRenderer({ original, enhanced }: { original: string; enhanced: string }) {
  const origParas = splitParagraphs(original)
  const enhParas  = splitParagraphs(enhanced)

  // For short text (≤ 1 paragraph each), just do word diff directly
  if (origParas.length <= 1 && enhParas.length <= 1) {
    return (
      <div className="p-2.5">
        <p className="text-xs leading-relaxed whitespace-pre-wrap break-words">
          <InlineWordDiff original={original} enhanced={enhanced} />
        </p>
      </div>
    )
  }

  const blocks = computeParagraphDiff(original, enhanced)
  return (
    <div className="divide-y divide-border/20">
      {blocks.map((block, i) => {
        if (block.type === "equal") {
          return (
            <div key={i} className="px-3 py-2 text-xs text-muted-foreground/70 leading-relaxed">
              {block.enhanced}
            </div>
          )
        }
        if (block.type === "delete") {
          return (
            <div key={i} className="bg-red-500/8 border-l-2 border-red-500/50 px-3 py-2">
              <p className="text-xs text-red-300/80 line-through leading-relaxed">{block.original}</p>
            </div>
          )
        }
        if (block.type === "insert") {
          return (
            <div key={i} className="bg-emerald-500/8 border-l-2 border-emerald-500/50 px-3 py-2">
              <p className="text-xs text-emerald-300/80 leading-relaxed">{block.enhanced}</p>
            </div>
          )
        }
        // replace — show inline word diff within the paragraph
        return (
          <div key={i} className="bg-violet-500/5 border-l-2 border-violet-500/30 px-3 py-2">
            <p className="text-xs leading-relaxed">
              <InlineWordDiff original={block.original!} enhanced={block.enhanced!} />
            </p>
          </div>
        )
      })}
    </div>
  )
}

function LineDiffRenderer({ original, enhanced }: { original: string[]; enhanced: string[] }) {
  const ops = computeLineDiff(original, enhanced)

  return (
    <div className="py-1">
      {ops.map((op, i) => {
        if (op.type === "equal") {
          return (
            <div key={i} className="flex items-start gap-2 px-2.5 py-0.5">
              <span className="mt-0.5 text-[10px] font-mono text-muted-foreground/25 w-3 shrink-0 select-none">=</span>
              <span className="text-xs text-muted-foreground/60 leading-relaxed">{op.value}</span>
            </div>
          )
        }
        if (op.type === "delete") {
          return (
            <div key={i} className="flex items-start gap-2 px-2.5 py-0.5 bg-red-500/8 border-l-2 border-red-500/50">
              <span className="mt-0.5 text-[10px] font-mono text-red-400/60 w-3 shrink-0 select-none">−</span>
              <span className="text-xs text-red-300/80 line-through leading-relaxed">{op.value}</span>
            </div>
          )
        }
        return (
          <div key={i} className="flex items-start gap-2 px-2.5 py-0.5 bg-emerald-500/8 border-l-2 border-emerald-500/50">
            <span className="mt-0.5 text-[10px] font-mono text-emerald-400/60 w-3 shrink-0 select-none">+</span>
            <span className="text-xs text-emerald-300/80 leading-relaxed">{op.value}</span>
          </div>
        )
      })}
    </div>
  )
}

// ── Main Component ─────────────────────────────────────────────────────────────

export function TextDiffView({ original, enhanced, isArrayField, className }: TextDiffViewProps) {
  if (isArrayField) {
    const origLines = Array.isArray(original)
      ? original
      : String(original).split("\n").filter(Boolean)
    const enhLines = Array.isArray(enhanced)
      ? enhanced
      : String(enhanced).split("\n").filter(Boolean)

    return (
      <div className={cn("overflow-hidden", className)}>
        <LineDiffRenderer original={origLines} enhanced={enhLines} />
      </div>
    )
  }

  const origStr = Array.isArray(original) ? original.join("\n") : String(original)
  const enhStr  = Array.isArray(enhanced)  ? enhanced.join("\n")  : String(enhanced)

  return (
    <div className={cn("overflow-hidden", className)}>
      <ParagraphDiffRenderer original={origStr} enhanced={enhStr} />
    </div>
  )
}
