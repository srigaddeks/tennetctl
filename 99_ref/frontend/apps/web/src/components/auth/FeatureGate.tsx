"use client";

import React from "react";
import { useAccess } from "@/components/providers/AccessProvider";

interface FeatureGateProps {
  actionCode: string;
  scope?: "platform" | "org";
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export function FeatureGate({
  actionCode,
  scope = "platform",
  fallback = null,
  children,
}: FeatureGateProps) {
  const { hasPlatformAction, hasOrgAction, isLoading } = useAccess();

  if (isLoading) return null; // Can be swapped for a skeleton loader if needed

  const hasAccess =
    scope === "platform"
      ? hasPlatformAction(actionCode)
      : hasOrgAction(actionCode);

  return hasAccess ? <>{children}</> : <>{fallback}</>;
}
