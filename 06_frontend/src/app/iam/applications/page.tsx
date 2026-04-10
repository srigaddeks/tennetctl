"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { Briefcase, Pencil, Plus } from "lucide-react";
import { listApplications } from "@/lib/api";
import { useAuth } from "@/components/providers/auth-provider";
import { PageHeader, PageBody } from "@/components/shell/page-header";
import { Card, CardHeader, CardTitle } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";
import { EmptyState } from "@/components/ui/empty-state";
import {
  Table,
  TableHeader,
  TableBody,
  TableRow,
  TableHead,
  TableCell,
} from "@/components/ui/table";
import { CreateApplicationModal } from "@/features/iam/_components/create-application-modal";
import { EditApplicationModal } from "@/features/iam/_components/edit-application-modal";
import type { ApplicationData } from "@/types/api";

export default function IamApplicationsPage() {
  const auth = useAuth();
  const router = useRouter();

  const [applications, setApplications] = useState<ApplicationData[] | null>(null);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showCreate, setShowCreate] = useState(false);
  const [editingApplication, setEditingApplication] = useState<ApplicationData | null>(null);

  useEffect(() => {
    if (auth.status === "loading") return;
    if (auth.status === "unauthenticated") {
      setError("unauthenticated");
      setLoading(false);
      return;
    }
    fetchApplications();
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [auth.status]);

  function fetchApplications() {
    if (auth.status !== "authenticated") return;
    setLoading(true);
    listApplications(auth.accessToken)
      .then((res) => {
        if (res.ok) {
          setApplications(res.data.items);
          setTotal(res.data.total);
        } else {
          setError(res.error.message);
        }
      })
      .catch(() => setError("Network error."))
      .finally(() => setLoading(false));
  }

  const isAuthenticated = auth.status === "authenticated";

  return (
    <>
      <PageHeader
        breadcrumb={["IAM", "Applications"]}
        title="Applications"
        description="Client applications that integrate with the platform via API tokens."
        actions={
          isAuthenticated ? (
            <Button
              size="sm"
              onClick={() => setShowCreate(true)}
              data-testid="new-application-button"
            >
              <Plus className="size-3.5" />
              New Application
            </Button>
          ) : undefined
        }
      />

      <PageBody>
        <Card>
          <CardHeader>
            <CardTitle>
              All Applications
              {total > 0 && (
                <span className="ml-2 font-normal text-foreground-muted">({total})</span>
              )}
            </CardTitle>
          </CardHeader>

          {(loading || auth.status === "loading") && (
            <div className="space-y-2 p-4">
              {[...Array(5)].map((_, i) => (
                <Skeleton key={i} className="h-8 w-full" />
              ))}
            </div>
          )}

          {!loading && error === "unauthenticated" && (
            <EmptyState
              icon={<Briefcase />}
              title="Sign in required"
              description="Sign in to view applications."
              action={
                <Button size="sm" onClick={() => router.push("/iam")}>
                  Go to sign in
                </Button>
              }
            />
          )}

          {!loading && error && error !== "unauthenticated" && (
            <EmptyState
              icon={<Briefcase />}
              title="Could not load applications"
              description={error}
              action={
                <Button size="sm" variant="outline" onClick={fetchApplications}>
                  Retry
                </Button>
              }
            />
          )}

          {!loading && !error && (!applications || applications.length === 0) && (
            <EmptyState
              icon={<Briefcase />}
              title="No applications yet"
              description="Create your first application to enable API token-based integrations."
              action={
                isAuthenticated ? (
                  <Button size="sm" onClick={() => setShowCreate(true)} data-testid="new-application-empty">
                    <Plus className="size-3.5" />
                    New Application
                  </Button>
                ) : undefined
              }
            />
          )}

          {!loading && !error && applications && applications.length > 0 && (
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Name</TableHead>
                  <TableHead>Code</TableHead>
                  <TableHead>Category</TableHead>
                  <TableHead>Products</TableHead>
                  <TableHead>Tokens</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="w-16" />
                </TableRow>
              </TableHeader>
              <TableBody>
                {applications.map((app) => (
                  <TableRow key={app.id} data-testid={`application-row-${app.id}`}>
                    <TableCell className="font-medium">{app.name}</TableCell>
                    <TableCell className="font-mono text-[11px] text-foreground-muted">
                      {app.code}
                    </TableCell>
                    <TableCell>
                      <Badge variant="outline">
                        {app.category_label ?? app.category_code ?? "—"}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-sm text-foreground-muted">
                      {app.linked_product_count}
                    </TableCell>
                    <TableCell className="text-sm text-foreground-muted">
                      {app.active_token_count}
                    </TableCell>
                    <TableCell>
                      {app.is_active ? (
                        <Badge variant="success">active</Badge>
                      ) : (
                        <Badge variant="default">inactive</Badge>
                      )}
                    </TableCell>
                    <TableCell>
                      {isAuthenticated && (
                        <button
                          onClick={() => setEditingApplication(app)}
                          className="rounded-sm p-1 text-foreground-muted hover:bg-surface-3 hover:text-foreground"
                          aria-label={`Edit ${app.name}`}
                          data-testid={`edit-application-${app.id}`}
                        >
                          <Pencil className="size-3.5" />
                        </button>
                      )}
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          )}
        </Card>
      </PageBody>

      {showCreate && auth.status === "authenticated" && (
        <CreateApplicationModal
          accessToken={auth.accessToken}
          onCreated={(application) => {
            setApplications((prev) => (prev ? [application, ...prev] : [application]));
            setTotal((t) => t + 1);
            setShowCreate(false);
          }}
          onClose={() => setShowCreate(false)}
        />
      )}

      {editingApplication && auth.status === "authenticated" && (
        <EditApplicationModal
          application={editingApplication}
          accessToken={auth.accessToken}
          onUpdated={(updated) => {
            setApplications(
              (prev) => prev?.map((a) => (a.id === updated.id ? updated : a)) ?? null
            );
            setEditingApplication(null);
          }}
          onClose={() => setEditingApplication(null)}
        />
      )}
    </>
  );
}
