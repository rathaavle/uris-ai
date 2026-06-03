/** @type {import('tailwindcss').Config} */
export default {
  content: ["./index.html", "./src/**/*.{js,jsx}"],
  theme: {
    extend: {
      colors: {
        // Ocean Deep — URIS-AI brand palette
        b0: "#0a1628",
        b1: "#0f2040",
        b2: "#162d50",
        b2h: "#1e3a63",
        bd: "#1a3a5c",
        ba: "#3a6a8c",

        t1: "#e2f0f9",
        t2: "#7ab8d9",
        t3: "#3a6a8c",

        accent: "#00b4d8",
        "accent-h": "#0096c7",

        risk: {
          rendah: "#2dc653",
          sedang: "#f4a621",
          tinggi: "#f25c54",
          kritis: "#b44fd4",
        },
      },
      fontFamily: {
        sans: ["Plus Jakarta Sans", "sans-serif"],
        mono: ["JetBrains Mono", "monospace"],
      },
    },
  },
  plugins: [],
};
