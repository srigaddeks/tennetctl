import { Topbar } from "@/components/Topbar";

export default function ShopLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Topbar />
      <main className="flex-1 mx-auto w-full px-6 py-10" style={{ maxWidth: "var(--content-max)" }}>
        {children}
      </main>
      <footer
        className="border-t mt-16 py-8 text-sm text-center"
        style={{ borderColor: "var(--border)", color: "var(--text-muted)" }}
      >
        Soma Delights · Hyderabad · Cold-pressed wellness
      </footer>
    </div>
  );
}
