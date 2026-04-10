"use client";

import { useEffect, useState, useRef } from "react";
import { X } from "lucide-react";
import { createApplication, listCategories, type CategoryData } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ApplicationData } from "@/types/api";

type CreateApplicationModalProps = {
  accessToken: string;
  onCreated: (application: ApplicationData) => void;
  onClose: () => void;
};

export function CreateApplicationModal({ accessToken, onCreated, onClose }: CreateApplicationModalProps) {
  const [name, setName] = useState("");
  const [code, setCode] = useState("");
  const [categories, setCategories] = useState<CategoryData[]>([]);
  const [categoryId, setCategoryId] = useState<number | null>(null);
  const [description, setDescription] = useState("");
  const [slug, setSlug] = useState("");
  const [iconUrl, setIconUrl] = useState("");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    listCategories(accessToken, "application").then((res) => {
      if (res.ok) {
        setCategories(res.data.items);
        if (res.data.items.length > 0) setCategoryId(res.data.items[0].id);
      }
    });
  }, [accessToken]);

  function deriveCode(v: string): string {
    return v.toLowerCase().replace(/\s+/g, "_").replace(/[^a-z0-9_]/g, "");
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    if (categoryId == null) {
      setError("Select a category.");
      return;
    }
    setSubmitting(true);
    try {
      const res = await createApplication(accessToken, {
        code,
        name,
        category_id: categoryId,
        description: description || undefined,
        slug: slug || undefined,
        icon_url: iconUrl || undefined,
      });
      if (!res.ok) {
        setError(res.error.message);
        return;
      }
      onCreated(res.data);
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
          <h2 className="text-sm font-semibold">Create Application</h2>
          <button
            onClick={onClose}
            className="rounded-sm p-1 text-foreground-muted hover:bg-surface-3 hover:text-foreground"
            aria-label="Close"
            data-testid="create-application-close"
          >
            <X className="size-4" />
          </button>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4 p-5">
          <div className="space-y-1.5">
            <Label htmlFor="app-name">Name</Label>
            <Input
              id="app-name"
              data-testid="create-application-name"
              value={name}
              placeholder="My Application"
              onChange={(e) => {
                setName(e.target.value);
                if (!code) setCode(deriveCode(e.target.value));
              }}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="app-code">Code</Label>
            <Input
              id="app-code"
              data-testid="create-application-code"
              value={code}
              placeholder="my_application"
              onChange={(e) => setCode(deriveCode(e.target.value))}
              required
              className="font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="app-category">Category</Label>
            <select
              id="app-category"
              data-testid="create-application-category"
              value={categoryId ?? ""}
              onChange={(e) => setCategoryId(e.target.value ? Number(e.target.value) : null)}
              className="flex h-9 w-full rounded-md border border-border bg-surface px-3 py-1 text-sm text-foreground focus-visible:outline-none focus-visible:border-border-strong focus-visible:ring-1 focus-visible:ring-ring"
            >
              {categories.length === 0 && (
                <option value="" disabled>Loading categories…</option>
              )}
              {categories.map((c) => (
                <option key={c.id} value={c.id}>{c.label}</option>
              ))}
            </select>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="app-description">
              Description <span className="text-foreground-subtle">(optional)</span>
            </Label>
            <Input
              id="app-description"
              data-testid="create-application-description"
              value={description}
              placeholder="Short description of this application"
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="app-slug">
              Slug <span className="text-foreground-subtle">(optional)</span>
            </Label>
            <Input
              id="app-slug"
              data-testid="create-application-slug"
              value={slug}
              placeholder="my-application"
              onChange={(e) => setSlug(e.target.value)}
              className="font-mono"
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="app-icon-url">
              Icon URL <span className="text-foreground-subtle">(optional)</span>
            </Label>
            <Input
              id="app-icon-url"
              data-testid="create-application-icon-url"
              value={iconUrl}
              placeholder="https://example.com/icon.png"
              onChange={(e) => setIconUrl(e.target.value)}
            />
          </div>

          {error && (
            <p className="rounded-md border border-[color:var(--danger)]/30 bg-[color:var(--danger-bg)] px-3 py-2 text-xs text-[color:var(--danger)]">
              {error}
            </p>
          )}

          <div className="flex justify-end gap-2 pt-1">
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={onClose}
              data-testid="create-application-cancel"
            >
              Cancel
            </Button>
            <Button
              type="submit"
              size="sm"
              disabled={submitting}
              data-testid="create-application-submit"
            >
              {submitting ? "Creating…" : "Create Application"}
            </Button>
          </div>
        </form>
      </div>
    </div>
  );
}
