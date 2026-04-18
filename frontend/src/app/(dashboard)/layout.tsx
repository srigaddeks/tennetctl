import { Sidebar } from "@/components/sidebar";
import { TopBar } from "@/components/topbar";
import { ImpersonationBanner } from "@/features/iam/_components/impersonation-banner";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  return (
    <div className="flex min-h-dvh flex-col">
      <ImpersonationBanner />
      <TopBar />
      <div className="flex flex-1 overflow-hidden">
        <Sidebar />
        <main className="flex flex-1 flex-col overflow-hidden">{children}</main>
      </div>
    </div>
  );
}
