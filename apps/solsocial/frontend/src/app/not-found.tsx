import Link from "next/link";
import { SunMark, Wordmark } from "@/components/sun-mark";

export default function NotFound() {
  return (
    <div className="min-h-screen relative z-10 grid place-items-center px-8">
      <div className="max-w-2xl text-center rise">
        <div className="mx-auto mb-8" style={{ width: 200 }}>
          <SunMark size={200} />
        </div>
        <p className="kicker rule mb-4">404 · Off the map</p>
        <h1 className="display text-[72px] leading-[0.95] mb-6">
          Nothing on <span className="display-italic">this</span> page.
        </h1>
        <p className="text-[color:var(--ink-70)] mb-10 max-w-lg mx-auto">
          The link might have moved or it was never here. Head back to the front page,
          or start a new post — that usually fixes it.
        </p>
        <div className="flex items-center justify-center gap-3">
          <Link href="/" className="btn btn-ember">← Front page</Link>
          <Link href="/composer" className="btn">✍ Compose</Link>
        </div>
        <div className="mt-16">
          <Wordmark subtitle="est. 2026" />
        </div>
      </div>
    </div>
  );
}
