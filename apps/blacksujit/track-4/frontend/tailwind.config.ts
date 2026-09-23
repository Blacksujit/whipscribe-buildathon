import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./src/pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/components/**/*.{js,ts,jsx,tsx,mdx}",
    "./src/app/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        /* WhipScribe exact design tokens */
        brand: "#c5f44b",
        "brand-200": "#d8f5b0",
        "brand-700": "#a3dc2d",
        "v4-ink": "#0f172a",
        "v4-ink-muted": "#64748b",
        "v4-bg": "#ffffff",
        "v4-bg-alt": "#eefce8",
        "v4-border": "rgba(15, 23, 42, 0.08)",
        paper: "#ffffff",
        paper2: "#fafafa",
        v100: "#f8fafc",
        v300: "#cbd5e1",
        v500: "#94a3b8",
        v700: "#334155",
        v800: "#1e293b",
        v900: "#0f172a",
        rule: "#e2e8f0",
        ok: "#10b981",
        accent: "#f59e0b",
      },
      fontFamily: {
        sans: ['"Inter"', "-apple-system", "BlinkMacSystemFont", "system-ui", "sans-serif"],
        display: ['"DM Serif Display"', "Georgia", "serif"],
        mono: ['"JetBrains Mono"', "ui-monospace", "Menlo", "monospace"],
      },
      borderRadius: {
        lg: "16px",
        xl: "20px",
      },
      maxWidth: {
        content: "960px",
      },
      boxShadow: {
        card: "0 1px 2px rgba(15, 23, 42, 0.04), 0 4px 14px -2px rgba(15, 23, 42, 0.05), 0 18px 44px -18px rgba(15, 23, 42, 0.10)",
        "card-hover": "0 2px 6px rgba(15, 23, 42, 0.06), 0 10px 28px -4px rgba(15, 23, 42, 0.08), 0 32px 72px -22px rgba(51, 65, 85, 0.22)",
      },
      transitionTimingFunction: {
        card: "cubic-bezier(0.22, 0.61, 0.36, 1)",
      },
      animation: {
        "fade-in-up": "fadeInUp 0.32s cubic-bezier(0.22, 0.61, 0.36, 1)",
      },
      keyframes: {
        fadeInUp: {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
      },
    },
  },
  plugins: [],
};

export default config;
