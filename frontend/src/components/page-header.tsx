export function PageHeader({
  title,
  description,
  actions,
  testId,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  testId?: string;
}) {
  return (
    <div className="flex flex-col gap-3 border-b border-zinc-200 bg-white px-8 py-6 sm:flex-row sm:items-start sm:justify-between dark:border-zinc-800 dark:bg-zinc-950">
      <div>
        <h1
          className="text-xl font-semibold tracking-tight text-zinc-900 dark:text-zinc-50"
          data-testid={testId}
        >
          {title}
        </h1>
        {description && (
          <p className="mt-1 max-w-2xl text-sm text-zinc-500 dark:text-zinc-400">
            {description}
          </p>
        )}
      </div>
      {actions && <div className="flex items-center gap-2">{actions}</div>}
    </div>
  );
}
