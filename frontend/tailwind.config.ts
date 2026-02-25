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
        background: "#0a0c10", // Ultra dark deep blue/black
        surface: "#11151c", // Elevated panel color
        surfaceHighlight: "#181d26", // Hover panel color
        primary: "#00f0ff", // Surgical Neon Cyan
        primaryVibrant: "#00d5ff",
        primaryMuted: "rgba(0, 240, 255, 0.15)",
        secondary: "#00ff9d", // Bioluminescent Green (for moderate/good states)
        danger: "#ff3366", // Neon Crimson (for high risk)
        warning: "#ffd166",
        textMain: "#e2e8f0",
        textMuted: "#94a3b8",
        borderDark: "rgba(255,255,255,0.08)",
      },
      backgroundImage: {
        'gradient-radial': 'radial-gradient(var(--tw-gradient-stops))',
        'hero-glow': 'radial-gradient(ellipse at top, rgba(0, 240, 255, 0.15), transparent 70%)',
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.5)',
        'neon': '0 0 20px rgba(0, 240, 255, 0.2)',
      }
    },
  },
  plugins: [],
};
export default config;
