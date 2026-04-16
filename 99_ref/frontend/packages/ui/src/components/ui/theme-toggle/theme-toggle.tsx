"use client";

import * as React from "react";
import { useTheme } from "next-themes";
import { cn } from "../../../lib/utils";
import { Moon as MoonIcon, Sun as SunIcon } from "lucide-react";

export function ThemeToggle() {
  const [mounted, setMounted] = React.useState(false);
  const { theme, resolvedTheme, setTheme } = useTheme();

  // Avoid hydration mismatch
  React.useEffect(() => {
    setMounted(true);
  }, []);

  const isDark = resolvedTheme === "dark" || theme === "dark";

  const toggle = () => setTheme(isDark ? "light" : "dark");

  if (!mounted) {
    return (
      <button
        aria-label="Toggle between dark and light mode"
        className="relative inline-flex h-6 w-12 shrink-0 cursor-not-allowed items-center rounded-full border-2 border-transparent bg-[#4e5d72] transition-colors duration-300 opacity-50"
        disabled
      >
        <span className="absolute left-1.5 flex items-center justify-center opacity-0">
          <SunIcon className="size-3.5 text-white" aria-hidden="true" />
        </span>
        <span className="absolute right-1.5 flex items-center justify-center opacity-0">
          <MoonIcon className="size-3.5 text-white" aria-hidden="true" />
        </span>
        <span className="pointer-events-none relative z-10 h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform duration-300 translate-x-0" />
      </button>
    );
  }

  return (
    <button
      onClick={toggle}
      aria-label="Toggle between dark and light mode"
      className="relative inline-flex h-6 w-12 shrink-0 cursor-pointer items-center rounded-full border-2 border-transparent bg-[#4e5d72] transition-colors duration-300 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2"
    >
      {/* Sun icon — visible on left when in dark mode */}
      <span
        className={cn(
          "absolute left-1.5 flex items-center justify-center transition-opacity duration-300",
          isDark ? "opacity-100" : "opacity-0"
        )}
      >
        <SunIcon className="size-3.5 text-white" aria-hidden="true" />
      </span>

      {/* Moon icon — visible on right when in light mode */}
      <span
        className={cn(
          "absolute right-1.5 flex items-center justify-center transition-opacity duration-300",
          isDark ? "opacity-0" : "opacity-100"
        )}
      >
        <MoonIcon className="size-3.5 text-white" aria-hidden="true" />
      </span>

      {/* Plain white sliding thumb */}
      <span
        className={cn(
          "pointer-events-none relative z-10 h-5 w-5 rounded-full bg-white shadow-lg ring-0 transition-transform duration-300",
          isDark ? "translate-x-6" : "translate-x-0"
        )}
      />
    </button>
  );
}
