import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{js,ts,jsx,tsx,mdx}"],
  theme: {
    extend: {
      colors: {
        surface: "#0f1419",
        panel: "#1a2332",
        accent: "#22c55e",
        danger: "#ef4444",
      },
    },
  },
  plugins: [],
};
export default config;
