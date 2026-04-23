"use client";
import Link from "next/link";
import { SunMark, Wordmark } from "@/components/sun-mark";

const QUOTES = [
  { q: "Schedule less. Say more.", a: "almanac №1" },
  { q: "A good post is a small bonfire.", a: "almanac №42" },
  { q: "Tend the feed as you would a garden.", a: "almanac №7" },
];

export default function AuthLayout({ children }: { children: React.ReactNode }) {
  const quote = QUOTES[new Date().getDate() % QUOTES.length];
  return (
    <div className="min-h-screen relative z-10">
      <div className="grid grid-cols-1 lg:grid-cols-[1.1fr_1fr] min-h-screen">
        {/* LEFT — editorial side */}
        <section className="relative px-10 py-10 lg:px-16 lg:py-14 flex flex-col justify-between overflow-hidden">
          <header className="relative z-10 flex items-start justify-between">
            <Link href="/signin"><Wordmark subtitle="est. 2026" /></Link>
            <span className="kicker">vol. i · issue i</span>
          </header>

          <div className="relative z-10 max-w-xl rise">
            <p className="kicker mb-6 rule">a publisher’s almanac</p>
            <h1 className="display text-[68px] md:text-[92px] lg:text-[112px]">
              The feed,
              <br />
              <span className="display-italic">attended to</span>.
            </h1>
            <p className="mt-6 max-w-md text-[15px] text-[color:var(--ink-70)]">
              SolSocial is a quiet tool for planning, drafting, queuing, and shipping posts
              across LinkedIn, Twitter, and Instagram. Built on the tennetctl platform.
            </p>
          </div>

          <footer className="relative z-10 flex items-end justify-between">
            <figure className="max-w-sm" suppressHydrationWarning>
              <blockquote className="display-italic text-[20px] text-[color:var(--ink)] leading-snug">
                “{quote.q}”
              </blockquote>
              <figcaption className="kicker mt-2">{quote.a}</figcaption>
            </figure>
            <div className="kicker hidden lg:block" suppressHydrationWarning>
              № {String(new Date().getFullYear()).slice(-2)}·{String(new Date().getMonth() + 1).padStart(2, "0")}
            </div>
          </footer>

          {/* Sun watermark */}
          <div className="absolute -right-24 top-1/2 -translate-y-1/2 opacity-70 pointer-events-none">
            <SunMark size={640} />
          </div>
          {/* Diagonal editorial rules */}
          <div className="absolute inset-0 pointer-events-none">
            <svg width="100%" height="100%" className="opacity-40">
              <line x1="0" y1="50%" x2="100%" y2="50%" stroke="var(--rule)" strokeWidth="0.5" />
              <line x1="0" y1="70%" x2="100%" y2="70%" stroke="var(--rule)" strokeDasharray="2 4" strokeWidth="0.5" />
            </svg>
          </div>
        </section>

        {/* RIGHT — form side */}
        <section className="paper-deep relative px-8 py-10 lg:px-14 lg:py-14 flex items-center">
          <div className="w-full max-w-sm mx-auto">{children}</div>
          <div className="absolute bottom-6 right-6 kicker">end of page</div>
          <div className="absolute top-0 left-0 right-0 h-px bg-[color:var(--rule)] lg:hidden" />
        </section>
      </div>
    </div>
  );
}
