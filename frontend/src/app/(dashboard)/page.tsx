import Link from "next/link";

import { PageHeader } from "@/components/page-header";
import { FEATURES } from "@/config/features";

const FEATURE_TONE: Record<string, string> = {
  iam: "bg-emerald-50 dark:bg-emerald-950/30",
  "feature-flags": "bg-blue-50 dark:bg-blue-950/30",
  nodes: "bg-purple-50 dark:bg-purple-950/30",
};

export default function Overview() {
  const features = FEATURES.filter((f) => f.key !== "overview");
  return (
    <div className="flex flex-1 flex-col">
      <PageHeader
        title="Overview"
        description="Self-hostable, workflow-native developer platform. Every top-level feature installed on this instance is listed below."
        testId="heading"
      />
      <div className="flex-1 overflow-y-auto px-8 py-6">
        <div className="grid grid-cols-1 gap-3 sm:grid-cols-2 lg:grid-cols-3">
          {features.map((f) => {
            const landing = f.subFeatures[0]?.href ?? f.basePath;
            return (
              <Link
                key={f.key}
                href={landing}
                className="group flex flex-col gap-2 rounded-xl border border-zinc-200 bg-white p-5 transition hover:border-zinc-900 hover:shadow-sm dark:border-zinc-800 dark:bg-zinc-950 dark:hover:border-zinc-100"
                data-testid={`overview-feature-${f.key}`}
              >
                <div className={`h-1 w-10 rounded-full ${FEATURE_TONE[f.key] ?? "bg-zinc-200"}`} />
                <div className="text-base font-semibold text-zinc-900 dark:text-zinc-50">
                  {f.label}
                </div>
                <p className="text-xs leading-relaxed text-zinc-500 dark:text-zinc-400">
                  {f.description}
                </p>
                <div className="mt-2 flex flex-wrap gap-1.5">
                  {f.subFeatures.map((s) => (
                    <span
                      key={s.href}
                      className="rounded-full border border-zinc-200 px-2 py-0.5 text-[10px] text-zinc-600 dark:border-zinc-800 dark:text-zinc-400"
                    >
                      {s.label}
                    </span>
                  ))}
                </div>
                <div className="mt-1 text-xs font-medium text-zinc-700 opacity-0 transition group-hover:opacity-100 dark:text-zinc-300">
                  Open →
                </div>
              </Link>
            );
          })}
        </div>
      </div>
    </div>
  );
}
