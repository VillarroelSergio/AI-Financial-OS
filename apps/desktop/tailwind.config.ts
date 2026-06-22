import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        "canvas-dark": "#000000",
        "surface-deep": "#0a0a0a",
        "surface-elevated": "#16181a",
        "surface-card": "#1e2124",
        primary: {
          DEFAULT: "#494fdf",
          bright: "#4f55f1",
        },
        "on-dark": {
          DEFAULT: "#ffffff",
          mute: "rgba(255,255,255,0.72)",
        },
        hairline: {
          dark: "rgba(255,255,255,0.12)",
          soft: "rgba(255,255,255,0.06)",
        },
        stone: "#8d969e",
        mute: "#505a63",
        accent: {
          teal: "#00a87e",
          danger: "#e23b4a",
          warning: "#ec7e00",
          yellow: "#b09000",
        },
      },
      fontFamily: {
        sans: ["Inter", "ui-sans-serif", "sans-serif"],
      },
      fontSize: {
        "display-lg": ["32px", { lineHeight: "1.19", fontWeight: "600", letterSpacing: "-0.32px" }],
        "heading-md": ["24px", { lineHeight: "1.33", fontWeight: "600" }],
        "heading-sm": ["20px", { lineHeight: "1.4", fontWeight: "500" }],
        "body-md": ["16px", { lineHeight: "1.5", fontWeight: "400", letterSpacing: "0.24px" }],
        "body-sm": ["14px", { lineHeight: "1.43", fontWeight: "400" }],
        "button-md": ["16px", { lineHeight: "1.5", fontWeight: "600", letterSpacing: "0.24px" }],
        caption: ["13px", { lineHeight: "1.4", fontWeight: "400" }],
      },
      borderRadius: {
        sm: "8px",
        md: "12px",
        lg: "20px",
        xl: "28px",
      },
      spacing: {
        xs: "6px",
        sm: "8px",
        md: "14px",
        lg: "16px",
        xl: "24px",
        "2xl": "32px",
        "3xl": "48px",
      },
    },
  },
  plugins: [],
} satisfies Config;
