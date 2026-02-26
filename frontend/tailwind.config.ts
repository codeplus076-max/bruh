import type { Config } from "tailwindcss";

const config: Config = {
  darkMode: "class",
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
        background: "rgb(var(--background) / <alpha-value>)",
        surface: "rgb(var(--surface) / <alpha-value>)",
        surfaceHighlight: "rgb(var(--surface-highlight) / <alpha-value>)",
        primary: "rgb(var(--primary) / <alpha-value>)",
        primaryVibrant: "rgb(var(--primary-vibrant) / <alpha-value>)",
        primaryMuted: "rgb(var(--primary) / 0.15)",
        secondary: "rgb(var(--secondary) / <alpha-value>)",
        danger: "rgb(var(--danger) / <alpha-value>)",
        warning: "rgb(var(--warning) / <alpha-value>)",
        textMain: "rgb(var(--text-main) / <alpha-value>)",
        textMuted: "rgb(var(--text-muted) / <alpha-value>)",
        borderDark: "rgb(var(--border-dark) / var(--border-opacity))",
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
