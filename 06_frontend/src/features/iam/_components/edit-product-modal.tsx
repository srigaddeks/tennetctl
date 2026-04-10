"use client";

import { useState, useRef } from "react";
import { X } from "lucide-react";
import { updateProduct } from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import type { ProductData } from "@/types/api";

type EditProductModalProps = {
  product: ProductData;
  accessToken: string;
  onUpdated: (product: ProductData) => void;
  onClose: () => void;
};

export function EditProductModal({ product, accessToken, onUpdated, onClose }: EditProductModalProps) {
  const [name, setName] = useState(product.name ?? "");
  const [description, setDescription] = useState(product.description ?? "");
  const [isSellable, setIsSellable] = useState(product.is_sellable);
  const [status, setStatus] = useState<string>(product.is_active ? "active" : "inactive");
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const backdropRef = useRef<HTMLDivElement>(null);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setSubmitting(true);
    try {
      const res = await updateProduct(
        product.id,
        {
          name: name || undefined,
          description: description || undefined,
          is_sellable: isSellable,
          status,
        },
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
          <h2 className="text-sm font-semibold">Edit Product</h2>
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
            <Label htmlFor="edit-product-code">Code</Label>
            <Input
              id="edit-product-code"
              value={product.code}
              readOnly
              className="font-mono text-xs opacity-60 cursor-not-allowed"
            />
            <p className="text-[11px] text-foreground-subtle">Code cannot be changed after creation.</p>
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-product-name">Name</Label>
            <Input
              id="edit-product-name"
              value={name}
              placeholder="My Product"
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-product-description">
              Description <span className="text-foreground-subtle">(optional)</span>
            </Label>
            <Input
              id="edit-product-description"
              value={description}
              placeholder="Short description"
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>

          <div className="space-y-1.5">
            <Label htmlFor="edit-product-status">Status</Label>
            <select
              id="edit-product-status"
              value={status}
              onChange={(e) => setStatus(e.target.value)}
              className="w-full rounded-md border border-border bg-surface px-3 py-1.5 text-sm focus:outline-none focus:ring-2 focus:ring-ring"
            >
              <option value="active">Active</option>
              <option value="inactive">Inactive</option>
            </select>
          </div>

          <div className="flex items-center gap-2">
            <input
              type="checkbox"
              id="edit-product-sellable"
              checked={isSellable}
              onChange={(e) => setIsSellable(e.target.checked)}
              className="size-4 rounded border-border accent-primary"
            />
            <Label htmlFor="edit-product-sellable" className="cursor-pointer">Sellable</Label>
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
