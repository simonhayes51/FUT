import type { Config } from "tailwindcss";

// FC Edge design tokens — premium dark, purple/blue gradients, neon accents.
const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        base: {
          950: "#0a0a12",
          900: "#0d0d18",
          850: "#11111f",
          800: "#16162a",
        },
        brand: {
          purple: "#8b5cf6",
          violet: "#a855f7",
          blue: "#3b82f6",
          cyan: "#22d3ee",
        },
        neon: {
          green: "#34d399",
          red: "#fb7185",
          amber: "#fbbf24",
        },
      },
      fontFamily: {
        sans: ["var(--font-sans)", "system-ui", "sans-serif"],
      },
      boxShadow: {
        glow: "0 0 40px -8px rgba(139, 92, 246, 0.45)",
        "glow-blue": "0 0 40px -8px rgba(59, 130, 246, 0.45)",
      },
      backgroundImage: {
        "brand-gradient":
          "linear-gradient(135deg, #8b5cf6 0%, #6366f1 45%, #3b82f6 100%)",
      },
      keyframes: {
        "fade-up": {
          "0%": { opacity: "0", transform: "translateY(8px)" },
          "100%": { opacity: "1", transform: "translateY(0)" },
        },
        shimmer: {
          "100%": { transform: "translateX(100%)" },
        },
      },
      animation: {
        "fade-up": "fade-up 0.4s ease-out both",
      },
    },
  },
  plugins: [],
};

export default config;
