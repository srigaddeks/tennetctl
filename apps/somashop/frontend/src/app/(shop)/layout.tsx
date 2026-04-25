import { Topbar } from "@/components/Topbar";

export default function ShopLayout({ children }: { children: React.ReactNode }) {
  return (
    <div className="min-h-screen flex flex-col">
      <Topbar />
      <main
        className="flex-1 mx-auto w-full px-6 py-10"
        style={{ maxWidth: "var(--content-max)" }}
      >
        {children}
      </main>
      <footer
        className="border-t mt-16 py-12"
        style={{ borderColor: "var(--border)" }}
      >
        <div
          className="mx-auto w-full px-6 grid grid-cols-1 md:grid-cols-3 gap-8 text-sm"
          style={{ maxWidth: "var(--content-max)" }}
        >
          <div>
            <p
              className="font-heading text-base font-bold mb-2"
              style={{ color: "var(--text-primary)" }}
            >
              Soma Delights
            </p>
            <p style={{ color: "var(--text-muted)" }}>
              Cold-pressed in Hyderabad. Delivered before breakfast.
            </p>
          </div>
          <div>
            <p
              className="text-xs tracking-[0.15em] uppercase mb-3"
              style={{ color: "var(--text-muted)" }}
            >
              The product
            </p>
            <ul className="space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>
                <a href="/products">Menu</a>
              </li>
              <li>
                <a href="/products">Subscription plans</a>
              </li>
              <li>
                <a href="/orders">Your orders</a>
              </li>
              <li>
                <a href="/profile">Account</a>
              </li>
            </ul>
          </div>
          <div>
            <p
              className="text-xs tracking-[0.15em] uppercase mb-3"
              style={{ color: "var(--text-muted)" }}
            >
              Reach us
            </p>
            <ul className="space-y-2" style={{ color: "var(--text-secondary)" }}>
              <li>WhatsApp: +91 9876 543 210</li>
              <li>Hours: 6 a.m. – 10 a.m., 7 days</li>
              <li>Hyderabad delivery only</li>
            </ul>
          </div>
        </div>
        <div
          className="mx-auto w-full px-6 mt-10 pt-6 border-t text-xs flex flex-wrap gap-4 justify-between"
          style={{
            maxWidth: "var(--content-max)",
            borderColor: "var(--border)",
            color: "var(--text-muted)",
          }}
        >
          <span>© Soma Delights · Powered by tennetctl</span>
          <span>FSSAI 12345 · Cold-chain certified</span>
        </div>
      </footer>
    </div>
  );
}
