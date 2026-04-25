"use client";

import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-20">
      {/* Hero */}
      <section className="text-center max-w-reading mx-auto">
        <p
          className="text-sm tracking-[0.2em] uppercase mb-6"
          style={{ color: "var(--text-muted)" }}
        >
          Cold-pressed wellness
        </p>
        <h1 className="font-heading text-5xl md:text-6xl font-extrabold leading-[1.05] tracking-tight">
          A quieter way to feel better.
        </h1>
        <p
          className="mt-6 text-lg leading-relaxed"
          style={{ color: "var(--text-secondary)" }}
        >
          Daily juices and shots, pressed in our Hyderabad kitchen at 4 a.m.,
          delivered before your morning. No HPP. No concentrates. Just produce.
        </p>
        <div className="mt-10 flex justify-center gap-4">
          <Link href="/products" className="btn btn-primary">
            See the menu
          </Link>
          <Link href="/signin" className="btn btn-ghost">
            Start a free week
          </Link>
        </div>
      </section>

      {/* Pull quote */}
      <section className="max-w-reading mx-auto">
        <blockquote className="pull-quote text-2xl leading-relaxed text-center">
          “Six ingredients. One step. Cold-pressed at 4 a.m. and at your door
          before breakfast.”
        </blockquote>
      </section>

      {/* Three pillars */}
      <section className="grid grid-cols-1 md:grid-cols-3 gap-8">
        {[
          {
            title: "Pressed at 4 a.m.",
            body: "Every batch is cold-pressed the same morning it's delivered. Nothing sits.",
          },
          {
            title: "Six ingredients or fewer",
            body: "If we can't pronounce it, it doesn't go in. Real produce, in Telugu kitchens, all day.",
          },
          {
            title: "Free first week",
            body: "We won't ask you to pay until you've tried six bottles. Cancel any time.",
          },
        ].map((p) => (
          <div key={p.title} className="card p-6">
            <h3 className="font-heading text-xl font-semibold mb-3">
              {p.title}
            </h3>
            <p className="leading-relaxed" style={{ color: "var(--text-secondary)" }}>
              {p.body}
            </p>
          </div>
        ))}
      </section>
    </div>
  );
}
