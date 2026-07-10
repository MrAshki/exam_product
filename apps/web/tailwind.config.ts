import type { Config } from "tailwindcss";

const config: Config = {
  content: [
    "./app/**/*.{ts,tsx}",
    "./components/**/*.{ts,tsx}",
    "./features/**/*.{ts,tsx}",
    "./lib/**/*.{ts,tsx}",
    "./stores/**/*.{ts,tsx}"
  ],
  theme: {
    extend: {
      colors: {
        ink: {
          900: "#111827",
          700: "#374151",
          500: "#6B7280"
        },
        surface: "#F8FAFC",
        brand: {
          50: "#ECFDF5",
          100: "#D1FAE5",
          600: "#059669",
          700: "#047857"
        },
        accent: {
          100: "#DBEAFE",
          600: "#2563EB"
        }
      },
      boxShadow: {
        soft: "0 1px 2px rgba(15, 23, 42, 0.06)"
      }
    }
  },
  plugins: []
};

export default config;
