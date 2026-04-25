"use client";

import Link from "next/link";

export default function HomePage() {
  return (
    <div className="space-y-24">
      {/* Hero */}
      <section className="text-center max-w-reading mx-auto">
        <p
          className="text-sm tracking-[0.2em] uppercase mb-6"
          style={{ color: "var(--text-muted)" }}
        >
          Cold-pressed wellness · Hyderabad
        </p>
        <h1 className="font-heading text-5xl md:text-6xl font-extrabold leading-[1.05] tracking-tight">
          A quieter way to feel better.
        </h1>
        <p
          className="mt-6 text-lg leading-relaxed"
          style={{ color: "var(--text-secondary)" }}
        >
          Daily juices and shots, pressed in our kitchen at 4 a.m., delivered
          before your morning. No HPP. No concentrates. Just produce.
        </p>
        <div className="mt-10 flex justify-center gap-4 flex-wrap">
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
            body: "Every batch is cold-pressed the same morning it's delivered. Nothing sits on a shelf.",
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
            <p
              className="leading-relaxed"
              style={{ color: "var(--text-secondary)" }}
            >
              {p.body}
            </p>
          </div>
        ))}
      </section>

      {/* How it works */}
      <section>
        <header className="max-w-reading mb-12">
          <p
            className="text-sm tracking-[0.2em] uppercase mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            How it works
          </p>
          <h2 className="font-heading text-3xl font-bold mb-4">
            One delivery, one cycle, no gym membership math.
          </h2>
        </header>
        <ol className="space-y-8 max-w-reading">
          {[
            {
              n: "01",
              t: "Pick your cadence",
              d: "Daily, 5x/week, or a wellness-warrior schedule. Three plans, ₹280–₹540 per delivery.",
            },
            {
              n: "02",
              t: "We press at 4 a.m.",
              d: "We squeeze your bottles in our Hyderabad kitchen the same morning, cold-pressed by a hydraulic press, never centrifugal.",
            },
            {
              n: "03",
              t: "Delivered before breakfast",
              d: "Insulated cold-chain delivery. Bottles arrive at your door between 6 and 10 a.m., 7 days a week.",
            },
            {
              n: "04",
              t: "You feel it by week two",
              d: "Most subscribers report better sleep, clearer skin, and steadier energy by their fourteenth bottle.",
            },
          ].map((s) => (
            <li key={s.n} className="flex gap-6 border-b pb-6"
                style={{ borderColor: "var(--border)" }}>
              <span
                className="font-mono text-sm pt-1"
                style={{ color: "var(--text-muted)" }}
              >
                {s.n}
              </span>
              <div>
                <h3 className="font-heading text-lg font-semibold mb-1">
                  {s.t}
                </h3>
                <p
                  className="leading-relaxed"
                  style={{ color: "var(--text-secondary)" }}
                >
                  {s.d}
                </p>
              </div>
            </li>
          ))}
        </ol>
      </section>

      {/* Testimonials */}
      <section>
        <header className="max-w-reading mb-12">
          <p
            className="text-sm tracking-[0.2em] uppercase mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            Said by subscribers
          </p>
          <h2 className="font-heading text-3xl font-bold mb-4">
            Word-of-mouth from Hyderabad.
          </h2>
        </header>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-8">
          {[
            {
              quote:
                "Three weeks in, my morning fog is gone. The ABC juice is the only thing I look forward to before my standup.",
              who: "Lakshmi · Banjara Hills · Daily Essentials",
            },
            {
              quote:
                "I tried the free week and never looked back. The amla shot is the best 60 seconds of my morning.",
              who: "Rahul · Jubilee Hills · Wellness Warrior",
            },
          ].map((t) => (
            <figure
              key={t.who}
              className="card p-8"
            >
              <blockquote
                className="pull-quote text-lg leading-relaxed mb-4"
              >
                "{t.quote}"
              </blockquote>
              <figcaption
                className="text-xs tracking-[0.15em] uppercase"
                style={{ color: "var(--text-muted)" }}
              >
                — {t.who}
              </figcaption>
            </figure>
          ))}
        </div>
      </section>

      {/* FAQ */}
      <section>
        <header className="max-w-reading mb-12">
          <p
            className="text-sm tracking-[0.2em] uppercase mb-3"
            style={{ color: "var(--text-muted)" }}
          >
            FAQ
          </p>
          <h2 className="font-heading text-3xl font-bold mb-4">
            Everything you'd ask before signing up.
          </h2>
        </header>
        <div className="space-y-6 max-w-reading">
          {[
            {
              q: "What's a cold-press, exactly?",
              a: "A hydraulic press squeezes the juice out of fruit and vegetables without heat or oxygen. The result keeps more vitamins, minerals, and live enzymes than centrifugal juicers, and stays good for 72 hours refrigerated.",
            },
            {
              q: "Can I pause my subscription when I travel?",
              a: "Yes. Reply to your last delivery confirmation message and we'll handle pause / resume / cancel. Self-serve subscription editing is coming.",
            },
            {
              q: "Do you deliver outside Hyderabad?",
              a: "Not yet. Our cold-chain only covers Hyderabad pin-codes today. Bengaluru is on the roadmap for Q3.",
            },
            {
              q: "Where do the ingredients come from?",
              a: "Telangana farms, where possible. Direct from the FSSAI-licensed mandi in Hyderabad otherwise. We reject any produce older than 24 hours.",
            },
            {
              q: "How do you handle plastic?",
              a: "Glass bottles, swapped on every delivery. Empties are washed, sterilised at 90°C, and refilled. Net-zero plastic per bottle by year three.",
            },
          ].map((f) => (
            <details
              key={f.q}
              className="card p-6"
              style={{ background: "var(--bg-surface)" }}
            >
              <summary
                className="font-heading text-lg font-semibold cursor-pointer"
                style={{ color: "var(--text-primary)" }}
              >
                {f.q}
              </summary>
              <p
                className="mt-4 leading-relaxed"
                style={{ color: "var(--text-secondary)" }}
              >
                {f.a}
              </p>
            </details>
          ))}
        </div>
      </section>

      {/* CTA strip */}
      <section
        className="text-center py-16 px-6 rounded"
        style={{
          background: "var(--bg-inverse)",
          color: "var(--text-on-inverse)",
        }}
      >
        <h2 className="font-heading text-4xl font-extrabold mb-4 tracking-tight">
          Start the week.
        </h2>
        <p className="mb-8 text-lg opacity-80 max-w-reading mx-auto">
          Free first week. Cancel any time. Delivery starts the morning after
          you sign up.
        </p>
        <Link
          href="/products"
          className="btn"
          style={{
            background: "var(--grey-0)",
            color: "var(--grey-900)",
            border: "1px solid var(--grey-0)",
          }}
        >
          See plans →
        </Link>
      </section>
    </div>
  );
}
