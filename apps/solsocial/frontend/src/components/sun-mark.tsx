// A typographic sun. Used as watermark on auth pages and as a brand mark.
// SVG-only; the outer ring "drifts" slowly, the ember dot "sways".

export function SunMark({ size = 240, className = "" }: { size?: number; className?: string }) {
  const s = size;
  const c = s / 2;
  const rays = Array.from({ length: 60 });
  return (
    <svg width={s} height={s} viewBox={`0 0 ${s} ${s}`} className={className} aria-hidden>
      <defs>
        <radialGradient id="sun-core" cx="50%" cy="50%" r="50%">
          <stop offset="0%"   stopColor="#FF8B4D" />
          <stop offset="60%"  stopColor="#DC4B19" />
          <stop offset="100%" stopColor="#9C2A07" />
        </radialGradient>
      </defs>

      {/* outer ring of minute ticks (drifts) */}
      <g className="drift" style={{ transformOrigin: `${c}px ${c}px` }}>
        {rays.map((_, i) => {
          const angle = (i / rays.length) * Math.PI * 2;
          const inner = s * 0.42;
          const outer = i % 5 === 0 ? s * 0.48 : s * 0.45;
          const x1 = c + Math.cos(angle) * inner;
          const y1 = c + Math.sin(angle) * inner;
          const x2 = c + Math.cos(angle) * outer;
          const y2 = c + Math.sin(angle) * outer;
          return (
            <line
              key={i}
              x1={x1} y1={y1} x2={x2} y2={y2}
              stroke="var(--ink)" strokeWidth={i % 5 === 0 ? 1.1 : 0.5}
              opacity={i % 5 === 0 ? 0.8 : 0.35}
            />
          );
        })}
      </g>

      {/* inner circle */}
      <circle cx={c} cy={c} r={s * 0.36} fill="none" stroke="var(--ink)" strokeWidth="1" opacity="0.8" />
      <circle cx={c} cy={c} r={s * 0.33} fill="none" stroke="var(--ink)" strokeWidth="0.5" opacity="0.35" />

      {/* ember core */}
      <g className="sway" style={{ transformOrigin: `${c}px ${c}px` }}>
        <circle cx={c} cy={c} r={s * 0.18} fill="url(#sun-core)" />
        <circle cx={c - s * 0.05} cy={c - s * 0.06} r={s * 0.035} fill="#FFD9B3" opacity="0.7" />
      </g>

      {/* compass N mark */}
      <text
        x={c} y={s * 0.08}
        textAnchor="middle"
        fill="var(--ink)"
        fontFamily="IBM Plex Mono, monospace"
        fontSize={s * 0.042}
        letterSpacing={s * 0.01}
      >
        N
      </text>
    </svg>
  );
}

export function Wordmark({ subtitle }: { subtitle?: string }) {
  return (
    <div className="inline-flex items-baseline gap-3">
      <span className="display text-[34px] leading-none tracking-tight">
        sol<span className="display-italic text-[var(--ember)]">·</span>social
      </span>
      {subtitle && <span className="kicker">{subtitle}</span>}
    </div>
  );
}
