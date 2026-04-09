"use client";

import { useRouter } from "next/navigation";
import * as React from "react";

export default function SettingsIndex() {
  const router = useRouter();
  React.useEffect(() => { router.replace("/settings/profile"); }, [router]);
  return null;
}
