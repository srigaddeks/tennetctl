"use client";

/**
 * Auto page-view tracker. Mount once near the root of the app — fires
 * page.viewed on every Next.js route change.
 */

import { usePathname, useSearchParams } from "next/navigation";
import { useEffect, useRef } from "react";

import { track, identify } from "@/lib/track";

export function PageViewTracker({
  actorUserId,
  orgId,
  workspaceId,
}: {
  actorUserId?: string | null;
  orgId?: string | null;
  workspaceId?: string | null;
}) {
  const pathname = usePathname();
  const searchParams = useSearchParams();
  const last = useRef<string | null>(null);

  // Persist identity for trackWithIdentity()
  useEffect(() => {
    identify(actorUserId ?? null, orgId ?? null, workspaceId ?? null);
  }, [actorUserId, orgId, workspaceId]);

  useEffect(() => {
    const url = pathname + (searchParams?.toString() ? `?${searchParams}` : "");
    if (last.current === url) return;
    last.current = url;
    track(
      "page.viewed",
      {
        path: pathname,
        query: searchParams ? Object.fromEntries(searchParams) : {},
        referrer: typeof document !== "undefined" ? document.referrer : "",
      },
      {
        url,
        actor_user_id: actorUserId ?? null,
        org_id: orgId ?? null,
        workspace_id: workspaceId ?? null,
      },
    );
  }, [pathname, searchParams, actorUserId, orgId, workspaceId]);

  return null;
}
