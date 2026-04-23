import { Breadcrumb, type BreadcrumbItem } from "@/components/breadcrumb";

export function PageHeader({
  title,
  description,
  actions,
  testId,
  breadcrumbs,
}: {
  title: string;
  description?: string;
  actions?: React.ReactNode;
  testId?: string;
  breadcrumbs?: BreadcrumbItem[];
}) {
  return (
    <div
      className="flex flex-col gap-2 border-b px-6 py-4 sm:flex-row sm:items-center sm:justify-between"
      style={{
        background: "var(--bg-surface)",
        borderColor: "var(--border)",
      }}
    >
      <div className="flex flex-col gap-1">
        {breadcrumbs && breadcrumbs.length > 0 && (
          <Breadcrumb items={breadcrumbs} />
        )}
        <div className="flex items-center gap-2">
          <div
            className="h-4 w-0.5 rounded-full"
            style={{ background: "var(--accent)" }}
            aria-hidden
          />
          <h1
            className="text-[15px] font-semibold tracking-wide"
            style={{ color: "var(--text-primary)" }}
            data-testid={testId}
          >
            {title}
          </h1>
        </div>
        {description && (
          <p
            className="text-[12px] leading-relaxed pl-3"
            style={{ color: "var(--text-muted)" }}
          >
            {description}
          </p>
        )}
      </div>
      {actions && (
        <div className="flex items-center gap-2 shrink-0">{actions}</div>
      )}
    </div>
  );
}
