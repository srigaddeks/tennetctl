"use client";

import { useCallback, useEffect, useMemo, useState } from "react";
import { useRouter } from "next/navigation";
import { Badge, Button, Card, CardContent, CardHeader, CardTitle, Separator } from "@kcontrol/ui";
import { ClipboardListIcon, LogOutIcon, RefreshCwIcon } from "lucide-react";
import { fetchMe, logoutUser } from "@/lib/api/auth";
import { getTask, listTasks, submitTaskForReview } from "@/lib/api/grc";
import type { TaskResponse } from "@/lib/types/grc";
import { useAccess } from "@/components/providers/AccessProvider";
import { CommentsSection } from "@/components/comments/CommentsSection";
import { AttachmentsSection } from "@/components/attachments/AttachmentsSection";

function formatDate(value: string | null | undefined): string {
  if (value == null) return "-";
  try {
    return new Date(value).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric",
    });
  } catch {
    return value;
  }
}

export default function AssigneeTasksPage() {
  const router = useRouter();
  const { refreshAccess } = useAccess();

  const [currentUserId, setCurrentUserId] = useState("");
  const [tasks, setTasks] = useState<TaskResponse[]>([]);
  const [selectedTaskId, setSelectedTaskId] = useState<string | null>(null);
  const [selectedTask, setSelectedTask] = useState<TaskResponse | null>(null);
  const [isBooting, setIsBooting] = useState(true);
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [isLoadingTask, setIsLoadingTask] = useState(false);
  const [isSubmittingReview, setIsSubmittingReview] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const selectedTaskSummary = useMemo(
    () => tasks.find((task) => task.id === selectedTaskId) ?? null,
    [selectedTaskId, tasks],
  );

  const loadPortal = useCallback(async () => {
    setIsRefreshing(true);
    try {
      const me = await fetchMe();
      setCurrentUserId(me.user_id);
      await refreshAccess().catch(() => undefined);
      const response = await listTasks({ limit: 200, sort_by: "due_date", sort_dir: "asc" });
      setTasks(response.items);
      setSelectedTaskId((prev) => {
        if (prev && response.items.some((task) => task.id === prev)) {
          return prev;
        }
        return response.items[0]?.id ?? null;
      });
      setError(null);
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to load assignee tasks.");
      router.replace("/assignee/login");
    } finally {
      setIsRefreshing(false);
      setIsBooting(false);
    }
  }, [refreshAccess, router]);

  useEffect(() => {
    void loadPortal();
  }, [loadPortal]);

  useEffect(() => {
    if (selectedTaskId == null) {
      setSelectedTask(null);
      return;
    }
    let cancelled = false;
    setIsLoadingTask(true);
    void getTask(selectedTaskId)
      .then((task) => {
        if (cancelled) return;
        setSelectedTask(task);
      })
      .catch((err: unknown) => {
        if (cancelled) return;
        setSelectedTask(null);
        setError(err instanceof Error ? err.message : "Failed to load task details.");
      })
      .finally(() => {
        if (cancelled) return;
        setIsLoadingTask(false);
      });

    return () => {
      cancelled = true;
    };
  }, [selectedTaskId]);

  if (isBooting) {
    return (
      <main className="min-h-screen bg-background p-4 md:p-6 lg:p-8">
        <div className="mx-auto max-w-6xl">
          <div className="text-sm text-muted-foreground">Loading your assigned tasks...</div>
        </div>
      </main>
    );
  }

  const canSubmitForReview = selectedTask != null && ["open", "in_progress", "overdue"].includes(selectedTask.status_code);

  return (
    <main className="min-h-screen bg-background p-4 md:p-6 lg:p-8">
      <div className="mx-auto max-w-6xl space-y-4">
        <header className="flex flex-wrap items-center justify-between gap-2">
          <div className="space-y-1">
            <h1 className="font-secondary text-2xl font-bold tracking-wide text-foreground">Assignee Portal</h1>
            <p className="text-sm text-muted-foreground">View and update only tasks assigned to you.</p>
          </div>
          <div className="flex items-center gap-2">
            <Button
              variant="outline"
              onClick={() => {
                void loadPortal();
              }}
              disabled={isRefreshing}
            >
              <RefreshCwIcon className={`size-4 ${isRefreshing ? "animate-spin" : ""}`} />
              Refresh
            </Button>
            <Button
              variant="outline"
              onClick={() => {
                void logoutUser();
              }}
            >
              <LogOutIcon className="size-4" />
              Logout
            </Button>
          </div>
        </header>

        {error ? (
          <div className="rounded-md border border-red-500/20 bg-red-100/10 px-3 py-2 text-sm text-red-500">{error}</div>
        ) : null}

        <div className="grid gap-4 lg:grid-cols-[320px_1fr]">
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="flex items-center gap-2 text-base">
                <ClipboardListIcon className="size-4 text-muted-foreground" />
                Assigned Tasks ({tasks.length})
              </CardTitle>
            </CardHeader>
            <CardContent className="space-y-2">
              {tasks.length === 0 ? (
                <div className="rounded-md border border-dashed border-border px-3 py-4 text-sm text-muted-foreground">
                  No tasks are currently assigned to you.
                </div>
              ) : (
                tasks.map((task) => {
                  const isSelected = selectedTaskId === task.id;
                  return (
                    <button
                      key={task.id}
                      type="button"
                      onClick={() => setSelectedTaskId(task.id)}
                      className={`w-full rounded-md border p-3 text-left transition-colors ${
                        isSelected
                          ? "border-primary bg-primary/10"
                          : "border-border bg-card hover:bg-muted/40"
                      }`}
                    >
                      <div className="text-sm font-medium text-foreground line-clamp-2">
                        {task.title || "Untitled task"}
                      </div>
                      <div className="mt-2 flex items-center justify-between gap-2 text-xs">
                        <Badge variant="outline">{task.status_name || task.status_code}</Badge>
                        <span className="text-muted-foreground">Due {formatDate(task.due_date)}</span>
                      </div>
                    </button>
                  );
                })
              )}
            </CardContent>
          </Card>

          <section className="space-y-4">
            <Card>
              <CardHeader className="pb-3">
                <CardTitle className="text-base">
                  {selectedTaskSummary?.title || selectedTask?.title || "Select a task"}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {selectedTaskId == null ? (
                  <p className="text-sm text-muted-foreground">Choose a task from the list to see details.</p>
                ) : isLoadingTask ? (
                  <p className="text-sm text-muted-foreground">Loading task details...</p>
                ) : selectedTask == null ? (
                  <p className="text-sm text-muted-foreground">Task details are unavailable.</p>
                ) : (
                  <div className="space-y-3 text-sm">
                    <div className="flex flex-wrap items-center gap-2">
                      <Badge>{selectedTask.status_name || selectedTask.status_code}</Badge>
                      <Badge variant="outline">{selectedTask.priority_name || selectedTask.priority_code}</Badge>
                      <span className="text-muted-foreground">Due {formatDate(selectedTask.due_date)}</span>
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      <Button
                        size="sm"
                        onClick={() => {
                          if (!selectedTaskId || isSubmittingReview || !canSubmitForReview) return;
                          setIsSubmittingReview(true);
                          setError(null);
                          void submitTaskForReview(selectedTaskId)
                            .then((updated) => {
                              setSelectedTask(updated);
                              setTasks((prev) =>
                                prev.map((task) =>
                                  task.id === updated.id
                                    ? { ...task, status_code: updated.status_code, status_name: updated.status_name }
                                    : task,
                                ),
                              );
                            })
                            .catch((err: unknown) => {
                              setError(err instanceof Error ? err.message : "Failed to submit task for review.");
                            })
                            .finally(() => {
                              setIsSubmittingReview(false);
                            });
                        }}
                        disabled={!canSubmitForReview || isSubmittingReview}
                      >
                        {isSubmittingReview ? "Submitting..." : "Send for review and approval"}
                      </Button>
                      {!canSubmitForReview && (
                        <span className="text-xs text-muted-foreground">
                          Only open, in-progress, or overdue tasks can be submitted.
                        </span>
                      )}
                    </div>
                    <Separator />
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Description</p>
                      <p className="mt-1 text-foreground whitespace-pre-wrap">{selectedTask.description || "No description"}</p>
                    </div>
                    <div>
                      <p className="text-xs uppercase tracking-wide text-muted-foreground">Acceptance Criteria</p>
                      <p className="mt-1 text-foreground whitespace-pre-wrap">{selectedTask.acceptance_criteria || "No acceptance criteria"}</p>
                    </div>
                  </div>
                )}
              </CardContent>
            </Card>

            {selectedTaskId ? (
              <>
                <CommentsSection
                  entityType="task"
                  entityId={selectedTaskId}
                  currentUserId={currentUserId}
                  active={selectedTaskId != null}
                />
                <AttachmentsSection
                  entityType="task"
                  entityId={selectedTaskId}
                  currentUserId={currentUserId}
                  canUpload
                  active={selectedTaskId != null}
                />
              </>
            ) : null}
          </section>
        </div>
      </div>
    </main>
  );
}
