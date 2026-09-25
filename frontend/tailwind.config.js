/** @type {import('tailwindcss').Config} */
module.exports = {
  content: [
    "./app/**/*.{js,ts,jsx,tsx,mdx}",
    "./pages/**/*.{js,ts,jsx,tsx,mdx}",
    "./components/**/*.{js,ts,jsx,tsx,mdx}",
  ],
  theme: {
    extend: {
      colors: {
        accent: "#6366f1",
        "bg-base": "#080d18",
        "bg-surface": "#0f1626",
        "bg-elevated": "#151d30",
      },
      fontFamily: {
        sans: ["Inter", "system-ui", "-apple-system", "sans-serif"],
        mono: ["ui-monospace", "Cascadia Code", "monospace"],
      },
      backdropBlur: {
        xs: "4px",
      },
    },
  },
  plugins: [],
};