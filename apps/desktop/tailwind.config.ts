import type { Config } from "tailwindcss";

export default {
  content: ["./index.html", "./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        /* ── Paleta Apple nombrada ── */
        obsidian:      "#1d1d1f",
        "frost-white": "#f5f5f7",
        "pure-black":  "#000000",
        "paper-white": "#ffffff",
        carbon:        "#111111",
        platinum:      "#86868b",
        graphite:      "#333336",
        "silver-mist": "#cccccc",
        smoke:         "#424245",
        "apple-blue":  "#0071e3",
        "link-blue":   "#0066cc",
        "halo-blue":   "#2997ff",
        "signal-orange": "#f56900",
        "iris-violet": "#8668ff",
        "reef-teal":   "#00a1b3",

        /* ── Tokens semánticos → CSS vars (responden al tema) ── */
        "bg-app":          "var(--bg-app)",
        "bg-sidebar":      "var(--bg-sidebar)",
        "bg-surface":      "var(--bg-surface)",
        "bg-card":         "var(--bg-card)",
        "bg-card-elevated":"var(--bg-card-elevated)",
        "bg-interactive":  "var(--bg-interactive)",
        "border-soft":     "var(--border-soft)",
        "border-strong":   "var(--border-strong)",
        "divider-soft":    "var(--divider-soft)",
        "hairline-dark":   "var(--hairline-dark)",

        /* ── Aliases de compatibilidad (nombres antiguos → nuevos tokens) ── */
        /* Estos mantienen funcionando los TSX existentes sin cambios */
        ink:           "var(--text-primary)",
        charcoal:      "var(--text-secondary)",
        stone:         "var(--text-secondary)",
        mute:          "var(--text-muted)",
        "bone-cream":  "var(--bg-app)",
        "canvas-dark": "var(--bg-app)",
        "surface-deep":"var(--bg-surface)",
        "surface-elevated": "var(--bg-card-elevated)",
        "surface-card":"var(--bg-card)",

        primary: {
          DEFAULT: "var(--primary)",
          bright:  "var(--primary)",
        },
        "on-primary": "var(--on-primary)",
        "on-dark": {
          DEFAULT: "var(--text-primary)",
          mute:    "var(--text-secondary)",
        },
        hairline: {
          dark: "var(--hairline-dark)",
          soft: "var(--divider-soft)",
        },
        accent: {
          teal:    "var(--positive)",
          danger:  "var(--negative)",
          warning: "var(--warning)",
          yellow:  "var(--accent)",
        },

        /* ── Colores funcionales directos ── */
        "ember-orange": "#ff3d00",
      },

      fontFamily: {
        sans:    ["'SF Pro Text'", "Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        display: ["'SF Pro Display'", "Inter", "ui-sans-serif", "system-ui", "-apple-system", "BlinkMacSystemFont", "Segoe UI", "Roboto", "sans-serif"],
        mono:    ["'Courier New'", "ui-monospace", "monospace"],
      },

      fontSize: {
        /* Escala DESIGN.md */
        "caption":    ["10px", { lineHeight: "1.83", letterSpacing: "-0.37px" }],
        "body":       ["14px", { lineHeight: "1.43", letterSpacing: "-0.22px" }],
        "heading-sm": ["19px", { lineHeight: "1.21", letterSpacing: "-0.28px", fontWeight: "600" }],
        "heading":    ["24px", { lineHeight: "1.17", letterSpacing: "-0.24px", fontWeight: "600" }],
        "heading-lg": ["32px", { lineHeight: "1.14", letterSpacing: "-0.32px", fontWeight: "700" }],
        "display":    ["56px", { lineHeight: "1.07", letterSpacing: "-0.84px", fontWeight: "700" }],
        "hero":       ["80px", { lineHeight: "1.05", letterSpacing: "-0.24px", fontWeight: "700" }],

        /* Aliases de compatibilidad (mantienen TSX existentes) */
        "display-lg": ["56px", { lineHeight: "1.07", letterSpacing: "-0.84px", fontWeight: "700" }],
        "heading-md": ["32px", { lineHeight: "1.14", letterSpacing: "-0.32px", fontWeight: "700" }],
        "body-md":    ["17px", { lineHeight: "1.47", letterSpacing: "-0.22px" }],
        "body-sm":    ["14px", { lineHeight: "1.43", letterSpacing: "-0.22px" }],
        "button-md":  ["14px", { lineHeight: "1.43", letterSpacing: "-0.22px", fontWeight: "600" }],
      },

      borderRadius: {
        sm:    "10px",
        md:    "10px",
        lg:    "10px",
        xl:    "10px",
        "2xl": "28px",
        "3xl": "28px",
        "4xl": "36px",
        full:  "980px",
      },

      spacing: {
        xs:   "8px",
        sm:   "8px",
        md:   "16px",
        lg:   "24px",
        xl:   "28px",
        "2xl":"32px",
        "3xl":"48px",
        "4xl":"64px",
        "5xl":"80px",
      },
    },
  },
  plugins: [],
} satisfies Config;
