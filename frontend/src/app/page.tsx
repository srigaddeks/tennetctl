export default function Home() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center bg-zinc-50 dark:bg-zinc-950">
      <main className="flex flex-col items-center gap-8 text-center">
        <div className="flex flex-col items-center gap-2">
          <h1
            className="text-4xl font-bold tracking-tight text-zinc-900 dark:text-zinc-50"
            data-testid="heading"
          >
            TennetCTL
          </h1>
          <p className="text-lg text-zinc-600 dark:text-zinc-400">
            Developer Platform
          </p>
        </div>

        <p className="max-w-md text-sm text-zinc-500 dark:text-zinc-500">
          Self-hostable, workflow-native. Replace your entire SaaS toolchain
          with one unified system built on node graphs.
        </p>

        <div className="flex items-center gap-3 text-xs text-zinc-400">
          <span className="rounded-full bg-emerald-100 px-2.5 py-0.5 font-medium text-emerald-700 dark:bg-emerald-900/30 dark:text-emerald-400">
            v0.0.0
          </span>
          <span>AGPL-3</span>
        </div>
      </main>
    </div>
  );
}
