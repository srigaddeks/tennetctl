import { Suspense } from "react";

import { OAuthCallback } from "@/features/auth/_components/oauth-callback";

export default function GithubCallbackPage() {
  return (
    <Suspense fallback={null}>
      <OAuthCallback provider="github" />
    </Suspense>
  );
}
