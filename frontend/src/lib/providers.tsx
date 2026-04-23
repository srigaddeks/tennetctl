"use client";

/**
 * Client-side providers — TanStack Query + Toast dispatcher.
 */

import { MutationCache, QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { useState } from "react";

import { ToastProvider } from "@/components/toast";
import { busToast } from "@/lib/toast-bus";
import { WorkspaceProvider } from "@/lib/workspace-context";

export function Providers({ children }: { children: React.ReactNode }) {
  const [queryClient] = useState(
    () =>
      new QueryClient({
        mutationCache: new MutationCache({
          onError: (error) => {
            const message =
              error instanceof Error
                ? error.message
                : "An unexpected error occurred";
            busToast(message, "error");
          },
        }),
        defaultOptions: {
          queries: {
            staleTime: 30_000,
            refetchOnWindowFocus: false,
            retry: 1,
          },
        },
      })
  );

  return (
    <QueryClientProvider client={queryClient}>
      <WorkspaceProvider>
        <ToastProvider>{children}</ToastProvider>
      </WorkspaceProvider>
    </QueryClientProvider>
  );
}
