import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      fontFamily: {
        sans: ["Inter", "system-ui", "sans-serif"],
        heading: ["Outfit", "Inter", "system-ui", "sans-serif"],
        quote: ["Lora", "Georgia", "serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
      maxWidth: {
        content: "1200px",
        reading: "680px",
      },
    },
  },
  plugins: [],
};
export default config;
