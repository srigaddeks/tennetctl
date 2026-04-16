export type Theme = "dark" | "light";

export function getStoredTheme(): Theme {
  if (typeof window === "undefined") return "dark";
  return (localStorage.getItem("kc-arch-theme") as Theme) ?? "dark";
}

export function setStoredTheme(theme: Theme): void {
  localStorage.setItem("kc-arch-theme", theme);
  document.documentElement.classList.toggle("light", theme === "light");
}
