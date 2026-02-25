import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
    "./lib/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      fontFamily: {
        sans: ["var(--font-outfit)", "var(--font-geist-sans)", "sans-serif"],
        heading: ["var(--font-syne)", "sans-serif"],
        mono: ["var(--font-geist-mono)", "monospace"],
      },
      colors: {
        background: "#f8fafc", // light gray background
        surface: "#ffffff", // white cards
        surfaceHighlight: "#f1f5f9",
        primary: "#2563eb", // blue-600
        primaryVibrant: "#3b82f6", // blue-500
        primaryMuted: "rgba(37, 99, 235, 0.1)",
        secondary: "#10b981", // emerald-500
        danger: "#ef4444", // red-500
        warning: "#f59e0b", // amber-500
        textMain: "#0f172a", // slate-900
        textMuted: "#64748b", // slate-500
        borderDark: "#e2e8f0", // slate-200
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'radial-gradient(ellipse at top, rgba(37, 99, 235, 0.05), transparent 70%)',
      },
      boxShadow: {
        'glass': '0 4px 20px rgba(0, 0, 0, 0.05)',
        'neon': '0 0 20px rgba(37, 99, 235, 0.2)',
        'card': '0 8px 30px rgba(0, 0, 0, 0.04)',
      }
    },
  },
  plugins: [],
};
export default config;
