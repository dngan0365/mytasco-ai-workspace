import type { Config } from "tailwindcss";

export default {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: { extend: { fontFamily: { sans: ["var(--font-manrope)", "sans-serif"] } } },
  plugins: [],
} satisfies Config;
