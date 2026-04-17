import { Suspense } from "react";

import { OAuthCallback } from "@/features/auth/_components/oauth-callback";

export default function GoogleCallbackPage() {
  return (
    <Suspense fallback={null}>
      <OAuthCallback provider="google" />
    </Suspense>
  );
}
