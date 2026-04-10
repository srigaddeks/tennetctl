"use client";

import { useState, useRef } from "react";
import { X } from "lucide-react";
import { updateGroup } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { GroupData } from "@/types/api";

type EditGroupModalProps = {
  group: GroupData;
  accessToken: string;
  onUpdated: (group: GroupData) => void;
  onClose: () => void;
};

export function EditGroupModal({ group, accessToken, onUpdated, onClose }: EditGroupModalProps) {
  const [name, setName] = useState(group.name ?? "");
  const [description, setDescription] = useState(group.description ?? "");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await updateGroup(
        group.id,
        { name: name || undefined, description: description || undefined },
        accessToken
      );
      if (!res.ok) {
        setError(res.error.message);
        return;
      }
      onUpdated(res.data);
    } catch {
      setError("Network error.");
    } finally {
      setSubmitting(false);
    }
  }

  return (
    <div
      ref={backdropRef}
      className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
      onClick={(e) => { if (e.target === backdropRef.current) onClose(); }}
    >
      <div className="relative w-full max-w-md rounded-md border border-border bg-surface shadow-xl">
        <div className="flex items-center justify-between border-b border-border px-5 py-4">
          <h2 className="text-sm font-semibold">Edit Group</h2>
          <button
            onClick={onClose}
            className="rounded-sm p-1 text-foreground-muted hover:bg-surface-3 hover:text-foreground"
            aria-label="Close"
          >
            <X className="size-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-5">
          <div className="space-y-1.5">
            <Label htmlFor="edit-group-slug">Slug</Label>
            <Input
              id="edit-group-slug"
              value={group.slug ?? ""}
              readOnly
              className="font-mono text-xs opacity-60 cursor-not-allowed"
            />
            <p className="text-[11px] text-foreground-subtle">Slug cannot be changed after creation.</p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-group-name">Name</Label>
            <Input
              id="edit-group-name"
              value={name}
              placeholder="Engineering"
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-group-description">
              Description <span className="text-foreground-subtle">(optional)</span>
            </Label>
            <Input
              id="edit-group-description"
              value={description}
              placeholder="Members of the engineering team"
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          {error && (
            <p className="rounded-md border border-[color:var(--danger)]/30 bg-[color:var(--danger-bg)] px-3 py-2 text-xs text-[color:var(--danger)]">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <Button type="button" variant="outline" size="sm" onClick={onClose}>
              Cancel
            </Button>
            <Button type="submit" size="sm" disabled={submitting}>
              {submitting ? "Saving…" : "Save Changes"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
