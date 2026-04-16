"use client";

import React, { createContext, useContext, useState, useCallback, useRef, useMemo } from "react";
import { fetchAccessContext } from "@/lib/api/access";
import { CURRENT_ENV } from "@/lib/config";
import type { AccessContextResponse } from "@/lib/types/access";

// ── Access level types ────────────────────────────────────────────────────────

export type OrgAccessLevel = "none" | "viewer" | "member" | "admin" | "super_admin";
export type WorkspaceAccessLevel = "none" | "viewer" | "contributor" | "admin";

// ── Context type ──────────────────────────────────────────────────────────────

interface AccessContextType {
  access: AccessContextResponse | null;
  isLoading: boolean;

  // Action checks (feature_code.action_code, e.g. "control_library.create")
  hasPlatformAction: (actionCode: string) => boolean;
  hasOrgAction: (actionCode: string) => boolean;
  hasWorkspaceAction: (actionCode: string) => boolean;

  // Feature-level checks (e.g. "control_library" — user has at least .view)
  hasFeature: (featureCode: string) => boolean;
  /** Check if user can perform write actions (create/update/delete) on a feature */
  canWrite: (featureCode: string) => boolean;

  // Role-level booleans
  isWorkspaceAdmin: boolean;
  isOrgAdmin: boolean;
  isSuperAdmin: boolean;

  // Access level helpers
  orgAccessLevel: OrgAccessLevel;
  workspaceAccessLevel: WorkspaceAccessLevel;

  // Re-fetch
  refreshAccess: (orgId?: string, workspaceId?: string) => Promise<void>;
  /** Called by OrgWorkspaceContext / SandboxOrgWorkspaceContext to sync selection */
  setOrgWorkspaceContext: (orgId: string, workspaceId: string) => void;
}

const AccessContext = createContext<AccessContextType | null>(null);

// ── Provider ──────────────────────────────────────────────────────────────────

export function AccessProvider({ children }: { children: React.ReactNode }) {
  const [access, setAccess] = useState<AccessContextResponse | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const currentOrgId = useRef<string>("");
  const currentWorkspaceId = useRef<string>("");
  const fetchId = useRef(0); // Prevent stale responses from overwriting newer ones

  const loadAccess = useCallback(async (orgId?: string, workspaceId?: string) => {
    const id = ++fetchId.current;
    try {
      setIsLoading(true);
      const data = await fetchAccessContext(orgId, workspaceId);
      // Only apply if this is still the latest request
      if (id === fetchId.current) setAccess(data);
    } catch {
      if (id === fetchId.current) setAccess(null);
    } finally {
      if (id === fetchId.current) setIsLoading(false);
    }
  }, []);

  const refreshAccess = useCallback(async (orgId?: string, workspaceId?: string) => {
    const org = orgId ?? currentOrgId.current;
    const ws = workspaceId ?? currentWorkspaceId.current;
    await loadAccess(org || undefined, ws || undefined);
  }, [loadAccess]);

  const setOrgWorkspaceContext = useCallback((orgId: string, workspaceId: string) => {
    if (orgId === currentOrgId.current && workspaceId === currentWorkspaceId.current) return;
    currentOrgId.current = orgId;
    currentWorkspaceId.current = workspaceId;
    loadAccess(orgId || undefined, workspaceId || undefined);
  }, [loadAccess]);

  const isActionEnabledForCurrentEnv = useCallback(
    (action: { env_dev: boolean; env_staging: boolean; env_prod: boolean }) => {
      if (CURRENT_ENV === "prod") return action.env_prod;
      if (CURRENT_ENV === "staging") return action.env_staging;
      return action.env_dev;
    },
    [],
  );

  // ── Action checks ────────────────────────────────────────────────────────

  const hasPlatformAction = useCallback((actionCode: string) =>
    access?.platform?.actions.some(
      (a) => `${a.feature_code}.${a.action_code}` === actionCode && isActionEnabledForCurrentEnv(a),
    ) ?? false,
  [access, isActionEnabledForCurrentEnv]);

  const hasOrgAction = useCallback((actionCode: string) =>
    access?.current_org?.actions.some(
      (a) => `${a.feature_code}.${a.action_code}` === actionCode && isActionEnabledForCurrentEnv(a),
    ) ?? false,
  [access, isActionEnabledForCurrentEnv]);

  const hasWorkspaceAction = useCallback((actionCode: string) =>
    access?.current_workspace?.actions.some(
      (a) => `${a.feature_code}.${a.action_code}` === actionCode && isActionEnabledForCurrentEnv(a),
    ) ?? false,
  [access, isActionEnabledForCurrentEnv]);

  // ── Feature-level checks ─────────────────────────────────────────────────

  /** True if user has ANY action on this feature across all scopes */
  const hasFeature = useCallback((featureCode: string) => {
    if (!access) return false;
    const check = (
      actions:
        | {
            feature_code: string;
            env_dev: boolean;
            env_staging: boolean;
            env_prod: boolean;
          }[]
        | undefined,
    ) => actions?.some((a) => a.feature_code === featureCode && isActionEnabledForCurrentEnv(a)) ?? false;
    return (
      check(access.platform?.actions) ||
      check(access.current_org?.actions) ||
      check(access.current_workspace?.actions) ||
      check(access.current_workspace?.product_actions)
    );
  }, [access, isActionEnabledForCurrentEnv]);

  /** True if user has create, update, or delete on this feature */
  const canWrite = useCallback((featureCode: string) => {
    if (!access) return false;
    const writeActions = ["create", "update", "delete", "assign", "revoke", "enable", "disable"];
    const check = (
      actions:
        | {
            feature_code: string;
            action_code: string;
            env_dev: boolean;
            env_staging: boolean;
            env_prod: boolean;
          }[]
        | undefined,
    ) =>
      actions?.some(
        (a) =>
          a.feature_code === featureCode &&
          writeActions.includes(a.action_code) &&
          isActionEnabledForCurrentEnv(a),
      ) ?? false;
    return (
      check(access.platform?.actions) ||
      check(access.current_org?.actions) ||
      check(access.current_workspace?.actions) ||
      check(access.current_workspace?.product_actions)
    );
  }, [access, isActionEnabledForCurrentEnv]);

  // ── Computed role booleans ────────────────────────────────────────────────

  const isSuperAdmin = useMemo(() =>
    access?.platform?.actions.some(
      (a) => a.feature_code === "org_management" && a.action_code === "create"
    ) ?? false,
  [access]);

  const isOrgAdmin = useMemo(() =>
    access?.current_org?.actions.some(
      (a) => a.feature_code === "org_management" && a.action_code === "update"
    ) ?? false,
  [access]);

  const isWorkspaceAdmin = useMemo(() =>
    access?.current_workspace?.actions.some(
      (a) => a.feature_code === "workspace_management" && a.action_code === "update"
    ) ?? false,
  [access]);

  // ── Access level helpers ─────────────────────────────────────────────────

  const orgAccessLevel = useMemo((): OrgAccessLevel => {
    if (isSuperAdmin) return "super_admin";
    if (!access?.current_org) return "none";
    const orgActions = access.current_org.actions;
    if (orgActions.some((a) => a.feature_code === "org_management" && a.action_code === "update")) return "admin";
    if (orgActions.some((a) => a.feature_code === "workspace_management" && a.action_code === "create")) return "member";
    if (orgActions.some((a) => a.feature_code === "org_management" && a.action_code === "view")) return "viewer";
    return "none";
  }, [access, isSuperAdmin]);

  const workspaceAccessLevel = useMemo((): WorkspaceAccessLevel => {
    if (!access?.current_workspace) return "none";
    const wsActions = access.current_workspace.actions;
    if (wsActions.some((a) => a.feature_code === "workspace_management" && a.action_code === "update")) return "admin";
    if (wsActions.some((a) => a.feature_code === "workspace_management" && a.action_code === "update")) return "contributor";
    if (wsActions.some((a) => a.feature_code === "workspace_management" && a.action_code === "view")) return "viewer";
    return "none";
  }, [access]);

  return (
    <AccessContext.Provider
      value={{
        access,
        isLoading,
        hasPlatformAction,
        hasOrgAction,
        hasWorkspaceAction,
        hasFeature,
        canWrite,
        isWorkspaceAdmin,
        isOrgAdmin,
        isSuperAdmin,
        orgAccessLevel,
        workspaceAccessLevel,
        refreshAccess,
        setOrgWorkspaceContext,
      }}
    >
      {children}
    </AccessContext.Provider>
  );
}

export const useAccess = () => {
  const ctx = useContext(AccessContext);
  if (!ctx) throw new Error("useAccess must be used within an AccessProvider");
  return ctx;
};
