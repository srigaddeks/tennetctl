"use client";

import { useEffect, useState, useRef } from "react";
import { X, Plus, Unlink, RotateCcw, Trash2 } from "lucide-react";
import {
  updateApplication,
  listApplicationProducts,
  linkApplicationProduct,
  unlinkApplicationProduct,
  listApplicationTokens,
  createApplicationToken,
  rotateApplicationToken,
  revokeApplicationToken,
  listProducts,
} from "@/lib/api";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Badge } from "@/components/ui/badge";
import { AppTokenIssuedModal } from "./app-token-issued-modal";
import type {
  ApplicationData,
  ApplicationProductLinkData,
  ApplicationTokenData,
  ProductData,
} from "@/types/api";

type Tab = "general" | "products" | "tokens";

type EditApplicationModalProps = {
  application: ApplicationData;
  accessToken: string;
  onUpdated: (application: ApplicationData) => void;
  onClose: () => void;
};

export function EditApplicationModal({
  application,
  accessToken,
  onUpdated,
  onClose,
}: EditApplicationModalProps) {
  const [activeTab, setActiveTab] = useState<Tab>("general");
  const backdropRef = useRef<HTMLDivElement>(null);

  // General tab state
  const [name, setName] = useState(application.name ?? "");
  const [description, setDescription] = useState(application.description ?? "");
  const [slug, setSlug] = useState(application.slug ?? "");
  const [iconUrl, setIconUrl] = useState(application.icon_url ?? "");
  const [isActive, setIsActive] = useState(application.is_active);
  const [generalSubmitting, setGeneralSubmitting] = useState(false);
  const [generalError, setGeneralError] = useState<string | null>(null);

  // Products tab state
  const [linkedProducts, setLinkedProducts] = useState<ApplicationProductLinkData[]>([]);
  const [allProducts, setAllProducts] = useState<ProductData[]>([]);
  const [productsLoading, setProductsLoading] = useState(false);
  const [showLinkProduct, setShowLinkProduct] = useState(false);
  const [linkProductId, setLinkProductId] = useState("");
  const [linkingProduct, setLinkingProduct] = useState(false);
  const [productsError, setProductsError] = useState<string | null>(null);

  // Tokens tab state
  const [tokens, setTokens] = useState<ApplicationTokenData[]>([]);
  const [tokensLoading, setTokensLoading] = useState(false);
  const [tokensError, setTokensError] = useState<string | null>(null);
  const [showIssueToken, setShowIssueToken] = useState(false);
  const [newTokenName, setNewTokenName] = useState("");
  const [newTokenExpiry, setNewTokenExpiry] = useState("");
  const [issuingToken, setIssuingToken] = useState(false);
  const [issuedToken, setIssuedToken] = useState<string | null>(null);

  // Load products tab data on first switch
  useEffect(() => {
    if (activeTab === "products") {
      loadLinkedProducts();
      loadAllProducts();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  // Load tokens tab data on first switch
  useEffect(() => {
    if (activeTab === "tokens") {
      loadTokens();
    }
  // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [activeTab]);

  function loadLinkedProducts() {
    setProductsLoading(true);
    setProductsError(null);
    listApplicationProducts(accessToken, application.id)
      .then((res) => {
        if (res.ok) setLinkedProducts(res.data.items);
        else setProductsError(res.error.message);
      })
      .catch(() => setProductsError("Network error."))
      .finally(() => setProductsLoading(false));
  }

  function loadAllProducts() {
    listProducts(accessToken).then((res) => {
      if (res.ok) setAllProducts(res.data.items);
    });
  }

  function loadTokens() {
    setTokensLoading(true);
    setTokensError(null);
    listApplicationTokens(accessToken, application.id)
      .then((res) => {
        if (res.ok) setTokens(res.data.items);
        else setTokensError(res.error.message);
      })
      .catch(() => setTokensError("Network error."))
      .finally(() => setTokensLoading(false));
  }

  async function handleGeneralSubmit(e: React.FormEvent) {
    e.preventDefault();
    setGeneralError(null);
    setGeneralSubmitting(true);
    try {
      const res = await updateApplication(accessToken, application.id, {
        name: name || undefined,
        description: description || undefined,
        slug: slug || undefined,
        icon_url: iconUrl || undefined,
        is_active: isActive,
      });
      if (!res.ok) {
        setGeneralError(res.error.message);
        return;
      }
      onUpdated(res.data);
    } catch {
      setGeneralError("Network error.");
    } finally {
      setGeneralSubmitting(false);
    }
  }

  async function handleUnlinkProduct(productId: string) {
    const res = await unlinkApplicationProduct(accessToken, application.id, productId);
    if (res.ok) {
      setLinkedProducts((prev) => prev.filter((lp) => lp.product_id !== productId));
    }
  }

  async function handleLinkProduct() {
    if (!linkProductId) return;
    setLinkingProduct(true);
    try {
      const res = await linkApplicationProduct(accessToken, application.id, linkProductId);
      if (res.ok) {
        setLinkedProducts((prev) => [...prev, res.data]);
        setLinkProductId("");
        setShowLinkProduct(false);
      } else {
        setProductsError(res.error.message);
      }
    } catch {
      setProductsError("Network error.");
    } finally {
      setLinkingProduct(false);
    }
  }

  async function handleRevokeToken(tokenId: string) {
    const res = await revokeApplicationToken(accessToken, application.id, tokenId);
    if (res.ok) {
      setTokens((prev) => prev.filter((t) => t.id !== tokenId));
    }
  }

  async function handleRotateToken(tokenId: string) {
    const res = await rotateApplicationToken(accessToken, application.id, tokenId);
    if (res.ok) {
      setIssuedToken(res.data.token);
      setTokens((prev) =>
        prev.map((t) => (t.id === tokenId ? { ...res.data } : t))
      );
    }
  }

  async function handleIssueToken(e: React.FormEvent) {
    e.preventDefault();
    if (!newTokenName) return;
    setIssuingToken(true);
    try {
      const res = await createApplicationToken(accessToken, application.id, {
        name: newTokenName,
        expires_at: newTokenExpiry || undefined,
      });
      if (!res.ok) {
        setTokensError(res.error.message);
        return;
      }
      setIssuedToken(res.data.token);
      setTokens((prev) => [res.data, ...prev]);
      setNewTokenName("");
      setNewTokenExpiry("");
      setShowIssueToken(false);
    } catch {
      setTokensError("Network error.");
    } finally {
      setIssuingToken(false);
    }
  }

  const unlinkedProducts = allProducts.filter(
    (p) => !linkedProducts.some((lp) => lp.product_id === p.id)
  );

  const tabClass = (tab: Tab) =>
    `px-3 py-1.5 text-xs font-medium rounded-sm transition-colors ${
      activeTab === tab
        ? "bg-surface-3 text-foreground"
        : "text-foreground-muted hover:text-foreground hover:bg-surface-2"
    }`;

  return (
    <>
      <div
        ref={backdropRef}
        className="fixed inset-0 z-50 flex items-center justify-center bg-black/50"
        onClick={(e) => { if (e.target === backdropRef.current) onClose(); }}
      >
        <div className="relative w-full max-w-lg rounded-md border border-border bg-surface shadow-xl">
          <div className="flex items-center justify-between border-b border-border px-5 py-4">
            <div>
              <h2 className="text-sm font-semibold">Edit Application</h2>
              <p className="mt-0.5 font-mono text-[11px] text-foreground-muted">{application.code}</p>
            </div>
            <button
              onClick={onClose}
              className="rounded-sm p-1 text-foreground-muted hover:bg-surface-3 hover:text-foreground"
              aria-label="Close"
              data-testid="edit-application-close"
            >
              <X className="size-4" />
            </button>
          </div>

          {/* Tab bar */}
          <div className="flex gap-1 border-b border-border px-5 py-2">
            <button
              className={tabClass("general")}
              onClick={() => setActiveTab("general")}
              data-testid="edit-application-tab-general"
            >
              General
            </button>
            <button
              className={tabClass("products")}
              onClick={() => setActiveTab("products")}
              data-testid="edit-application-tab-products"
            >
              Products
            </button>
            <button
              className={tabClass("tokens")}
              onClick={() => setActiveTab("tokens")}
              data-testid="edit-application-tab-tokens"
            >
              Tokens
            </button>
          </div>

          {/* General tab */}
          {activeTab === "general" && (
            <form onSubmit={handleGeneralSubmit} className="space-y-4 p-5">
              <div className="space-y-1.5">
                <Label htmlFor="edit-app-code">Code</Label>
                <Input
                  id="edit-app-code"
                  value={application.code}
                  readOnly
                  className="cursor-not-allowed font-mono text-xs opacity-60"
                />
                <p className="text-[11px] text-foreground-subtle">Code cannot be changed after creation.</p>
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="edit-app-name">Name</Label>
                <Input
                  id="edit-app-name"
                  data-testid="edit-application-name"
                  value={name}
                  placeholder="My Application"
                  onChange={(e) => setName(e.target.value)}
                  required
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="edit-app-description">
                  Description <span className="text-foreground-subtle">(optional)</span>
                </Label>
                <Input
                  id="edit-app-description"
                  data-testid="edit-application-description"
                  value={description}
                  placeholder="Short description"
                  onChange={(e) => setDescription(e.target.value)}
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="edit-app-slug">
                  Slug <span className="text-foreground-subtle">(optional)</span>
                </Label>
                <Input
                  id="edit-app-slug"
                  data-testid="edit-application-slug"
                  value={slug}
                  placeholder="my-application"
                  onChange={(e) => setSlug(e.target.value)}
                  className="font-mono"
                />
              </div>

              <div className="space-y-1.5">
                <Label htmlFor="edit-app-icon-url">
                  Icon URL <span className="text-foreground-subtle">(optional)</span>
                </Label>
                <Input
                  id="edit-app-icon-url"
                  data-testid="edit-application-icon-url"
                  value={iconUrl}
                  placeholder="https://example.com/icon.png"
                  onChange={(e) => setIconUrl(e.target.value)}
                />
              </div>

              <div className="flex items-center gap-2">
                <input
                  type="checkbox"
                  id="edit-app-active"
                  data-testid="edit-application-active"
                  checked={isActive}
                  onChange={(e) => setIsActive(e.target.checked)}
                  className="size-4 rounded border-border accent-primary"
                />
                <Label htmlFor="edit-app-active" className="cursor-pointer">Active</Label>
              </div>

              {generalError && (
                <p className="rounded-md border border-[color:var(--danger)]/30 bg-[color:var(--danger-bg)] px-3 py-2 text-xs text-[color:var(--danger)]">
                  {generalError}
                </p>
              )}

              <div className="flex justify-end gap-2 pt-1">
                <Button type="button" variant="outline" size="sm" onClick={onClose}>
                  Cancel
                </Button>
                <Button
                  type="submit"
                  size="sm"
                  disabled={generalSubmitting}
                  data-testid="edit-application-save"
                >
                  {generalSubmitting ? "Saving…" : "Save Changes"}
                </Button>
              </div>
            </form>
          )}

          {/* Products tab */}
          {activeTab === "products" && (
            <div className="space-y-4 p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-foreground-muted">
                  Linked Products ({linkedProducts.length})
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowLinkProduct((v) => !v)}
                  data-testid="link-product-button"
                >
                  <Plus className="size-3.5" />
                  Link Product
                </Button>
              </div>

              {showLinkProduct && (
                <div className="flex items-center gap-2 rounded-md border border-border bg-surface-2 px-3 py-2">
                  <select
                    value={linkProductId}
                    onChange={(e) => setLinkProductId(e.target.value)}
                    className="flex h-8 flex-1 rounded-sm border border-border bg-surface px-2 text-sm focus-visible:outline-none"
                    data-testid="link-product-select"
                  >
                    <option value="">Select a product…</option>
                    {unlinkedProducts.map((p) => (
                      <option key={p.id} value={p.id}>{p.name} ({p.code})</option>
                    ))}
                  </select>
                  <Button
                    size="sm"
                    onClick={handleLinkProduct}
                    disabled={!linkProductId || linkingProduct}
                    data-testid="link-product-confirm"
                  >
                    {linkingProduct ? "Linking…" : "Link"}
                  </Button>
                </div>
              )}

              {productsError && (
                <p className="rounded-md border border-[color:var(--danger)]/30 bg-[color:var(--danger-bg)] px-3 py-2 text-xs text-[color:var(--danger)]">
                  {productsError}
                </p>
              )}

              {productsLoading && (
                <p className="text-xs text-foreground-muted">Loading…</p>
              )}

              {!productsLoading && linkedProducts.length === 0 && (
                <p className="py-4 text-center text-xs text-foreground-muted">
                  No products linked yet.
                </p>
              )}

              {!productsLoading && linkedProducts.length > 0 && (
                <ul className="divide-y divide-border rounded-md border border-border">
                  {linkedProducts.map((lp) => {
                    const product = allProducts.find((p) => p.id === lp.product_id);
                    return (
                      <li
                        key={lp.id}
                        className="flex items-center justify-between px-3 py-2.5"
                        data-testid={`linked-product-row-${lp.product_id}`}
                      >
                        <div>
                          <span className="text-sm font-medium">
                            {product?.name ?? lp.product_id}
                          </span>
                          {product && (
                            <span className="ml-2 font-mono text-[11px] text-foreground-muted">
                              {product.code}
                            </span>
                          )}
                        </div>
                        <button
                          onClick={() => handleUnlinkProduct(lp.product_id)}
                          className="flex items-center gap-1 rounded-sm p-1 text-xs text-foreground-muted hover:bg-surface-3 hover:text-danger"
                          aria-label="Unlink product"
                          data-testid={`unlink-product-${lp.product_id}`}
                        >
                          <Unlink className="size-3.5" />
                          Unlink
                        </button>
                      </li>
                    );
                  })}
                </ul>
              )}
            </div>
          )}

          {/* Tokens tab */}
          {activeTab === "tokens" && (
            <div className="space-y-4 p-5">
              <div className="flex items-center justify-between">
                <span className="text-xs font-medium text-foreground-muted">
                  Tokens ({tokens.filter((t) => t.is_active).length} active)
                </span>
                <Button
                  size="sm"
                  variant="outline"
                  onClick={() => setShowIssueToken((v) => !v)}
                  data-testid="issue-token-button"
                >
                  <Plus className="size-3.5" />
                  Issue Token
                </Button>
              </div>

              {showIssueToken && (
                <form
                  onSubmit={handleIssueToken}
                  className="space-y-2 rounded-md border border-border bg-surface-2 p-3"
                >
                  <div className="space-y-1">
                    <Label htmlFor="new-token-name" className="text-xs">Token name</Label>
                    <Input
                      id="new-token-name"
                      data-testid="issue-token-name"
                      value={newTokenName}
                      placeholder="e.g. ci-deploy"
                      onChange={(e) => setNewTokenName(e.target.value)}
                      required
                      className="h-8 text-sm"
                    />
                  </div>
                  <div className="space-y-1">
                    <Label htmlFor="new-token-expiry" className="text-xs">
                      Expires at <span className="text-foreground-subtle">(optional, ISO 8601)</span>
                    </Label>
                    <Input
                      id="new-token-expiry"
                      data-testid="issue-token-expiry"
                      value={newTokenExpiry}
                      placeholder="2027-01-01T00:00:00Z"
                      onChange={(e) => setNewTokenExpiry(e.target.value)}
                      className="h-8 font-mono text-xs"
                    />
                  </div>
                  <div className="flex justify-end gap-2">
                    <Button
                      type="button"
                      variant="outline"
                      size="sm"
                      onClick={() => setShowIssueToken(false)}
                    >
                      Cancel
                    </Button>
                    <Button
                      type="submit"
                      size="sm"
                      disabled={issuingToken || !newTokenName}
                      data-testid="issue-token-submit"
                    >
                      {issuingToken ? "Issuing…" : "Issue"}
                    </Button>
                  </div>
                </form>
              )}

              {tokensError && (
                <p className="rounded-md border border-[color:var(--danger)]/30 bg-[color:var(--danger-bg)] px-3 py-2 text-xs text-[color:var(--danger)]">
                  {tokensError}
                </p>
              )}

              {tokensLoading && (
                <p className="text-xs text-foreground-muted">Loading…</p>
              )}

              {!tokensLoading && tokens.length === 0 && (
                <p className="py-4 text-center text-xs text-foreground-muted">
                  No tokens issued yet.
                </p>
              )}

              {!tokensLoading && tokens.length > 0 && (
                <ul className="divide-y divide-border rounded-md border border-border">
                  {tokens.map((t) => (
                    <li
                      key={t.id}
                      className="flex items-start justify-between gap-3 px-3 py-2.5"
                      data-testid={`token-row-${t.id}`}
                    >
                      <div className="min-w-0 flex-1">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-medium">{t.name}</span>
                          {t.is_active ? (
                            <Badge variant="success">active</Badge>
                          ) : (
                            <Badge variant="default">revoked</Badge>
                          )}
                        </div>
                        <div className="mt-0.5 flex items-center gap-2">
                          <span className="font-mono text-[11px] text-foreground-muted">
                            {t.token_prefix}…
                          </span>
                          {t.expires_at && (
                            <span className="text-[11px] text-foreground-muted">
                              expires {new Date(t.expires_at).toLocaleDateString()}
                            </span>
                          )}
                        </div>
                        {t.last_used_at && (
                          <p className="text-[11px] text-foreground-subtle">
                            last used {new Date(t.last_used_at).toLocaleDateString()}
                          </p>
                        )}
                      </div>
                      {t.is_active && (
                        <div className="flex shrink-0 gap-1">
                          <button
                            onClick={() => handleRotateToken(t.id)}
                            className="flex items-center gap-1 rounded-sm p-1 text-xs text-foreground-muted hover:bg-surface-3 hover:text-foreground"
                            aria-label="Rotate token"
                            data-testid={`rotate-token-${t.id}`}
                          >
                            <RotateCcw className="size-3.5" />
                            Rotate
                          </button>
                          <button
                            onClick={() => handleRevokeToken(t.id)}
                            className="flex items-center gap-1 rounded-sm p-1 text-xs text-foreground-muted hover:bg-surface-3 hover:text-danger"
                            aria-label="Revoke token"
                            data-testid={`revoke-token-${t.id}`}
                          >
                            <Trash2 className="size-3.5" />
                            Revoke
                          </button>
                        </div>
                      )}
                    </li>
                  ))}
                </ul>
              )}
            </div>
          )}
        </div>
      </div>

      {issuedToken && (
        <AppTokenIssuedModal
          token={issuedToken}
          onClose={() => setIssuedToken(null)}
        />
      )}
    </>
  );
}
