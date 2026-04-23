// Paper-toned skeletons that feel intentional, not "loading…"
// Uses the same warm paper-edge color as hairlines, at a quiet shimmer.

export function SkeletonLine({
  width = "100%", height = 14, className = "",
}: { width?: string | number; height?: number; className?: string }) {
  return (
    <div
      className={`animate-[shimmer_1.8s_linear_infinite] bg-[color:var(--paper-edge)] ${className}`}
      style={{
        width, height,
        backgroundImage: "linear-gradient(90deg, var(--paper-edge) 0%, var(--paper-deep) 40%, var(--paper-edge) 80%)",
        backgroundSize: "200% 100%",
      }}
    />
  );
}

export function SkeletonListRow() {
  return (
    <div className="grid grid-cols-[80px_1fr_200px] gap-6 py-5 items-center">
      <SkeletonLine width={60} height={10} />
      <div className="space-y-2">
        <SkeletonLine width="55%" height={22} />
        <SkeletonLine width="80%" height={14} />
      </div>
      <SkeletonLine width={90} height={10} className="justify-self-end" />
    </div>
  );
}

export function SkeletonList({ rows = 4 }: { rows?: number }) {
  return (
    <ul className="hairline-t">
      {Array.from({ length: rows }).map((_, i) => (
        <li key={i} className="hairline-b">
          <SkeletonListRow />
        </li>
      ))}
    </ul>
  );
}

export function SkeletonTiles({ count = 3 }: { count?: number }) {
  return (
    <div className="grid grid-cols-3 gap-0 hairline mb-16">
      {Array.from({ length: count }).map((_, i) => (
        <div key={i} className={`p-8 ${i > 0 ? "border-l border-[color:var(--rule)]" : ""}`}>
          <SkeletonLine width={100} height={10} />
          <div className="mt-5">
            <SkeletonLine width={60} height={56} />
          </div>
        </div>
      ))}
    </div>
  );
}

export function SkeletonCard() {
  return (
    <div className="paper p-6 space-y-3">
      <SkeletonLine width="40%" height={10} />
      <SkeletonLine width="80%" height={20} />
      <SkeletonLine width="100%" height={14} />
      <SkeletonLine width="60%" height={14} />
    </div>
  );
}
