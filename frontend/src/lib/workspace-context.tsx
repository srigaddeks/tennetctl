"use client";

/**
 * WorkspaceContext — org + workspace selection that follows the user session.
 *
 * Priority: localStorage override → session value → null
 * Persists selections across page loads. Falls back to session values on first load.
 */

import {
  createContext,
  useCallback,
  useContext,
  useEffect,
  useState,
  type ReactNode,
} from "react";

import { useMe } from "@/features/auth/hooks/use-auth";

const LS_ORG_KEY = "tennetctl_org_id";
const LS_WS_KEY  = "tennetctl_workspace_id";

export type WorkspaceContextValue = {
  orgId: string | null;
  workspaceId: string | null;
  setOrgId: (id: string | null) => void;
  setWorkspaceId: (id: string | null) => void;
};

const WorkspaceContext = createContext<WorkspaceContextValue | null>(null);

function readLs(key: string): string | null {
  if (typeof window === "undefined") return null;
  try {
    return localStorage.getItem(key);
  } catch {
    return null;
  }
}

function writeLs(key: string, value: string | null): void {
  if (typeof window === "undefined") return;
  try {
    if (value === null) {
      localStorage.removeItem(key);
    } else {
      localStorage.setItem(key, value);
    }
  } catch {
    // ignore quota errors
  }
}

export function WorkspaceProvider({ children }: { children: ReactNode }) {
  const me = useMe();
  const sessionOrgId = me.data?.session?.org_id ?? null;
  const sessionWsId  = me.data?.session?.workspace_id ?? null;

  // Initialise from localStorage; fall back to session once loaded
  const [orgId, setOrgIdState] = useState<string | null>(() => readLs(LS_ORG_KEY));
  const [workspaceId, setWorkspaceIdState] = useState<string | null>(() => readLs(LS_WS_KEY));
  const [seeded, setSeeded] = useState(false);

  // Once the session resolves, seed from session if localStorage had nothing
  useEffect(() => {
    if (seeded) return;
    if (!me.isSuccess) return;
    setSeeded(true);
    if (orgId === null && sessionOrgId !== null) {
      setOrgIdState(sessionOrgId);
    }
    if (workspaceId === null && sessionWsId !== null) {
      setWorkspaceIdState(sessionWsId);
    }
  }, [me.isSuccess, seeded, orgId, workspaceId, sessionOrgId, sessionWsId]);

  const setOrgId = useCallback((id: string | null) => {
    writeLs(LS_ORG_KEY, id);
    setOrgIdState(id);
    // Clear workspace when org changes
    writeLs(LS_WS_KEY, null);
    setWorkspaceIdState(null);
  }, []);

  const setWorkspaceId = useCallback((id: string | null) => {
    writeLs(LS_WS_KEY, id);
    setWorkspaceIdState(id);
  }, []);

  return (
    <WorkspaceContext.Provider value={{ orgId, workspaceId, setOrgId, setWorkspaceId }}>
      {children}
    </WorkspaceContext.Provider>
  );
}

export function useWorkspaceContext(): WorkspaceContextValue {
  const ctx = useContext(WorkspaceContext);
  if (!ctx) {
    throw new Error("useWorkspaceContext must be used inside <WorkspaceProvider>");
  }
  return ctx;
}
