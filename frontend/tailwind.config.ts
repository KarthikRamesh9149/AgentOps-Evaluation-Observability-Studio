import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./app/**/*.{ts,tsx}", "./components/**/*.{ts,tsx}", "./lib/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        ink: "#172026",
        panel: "#f7f9fc",
        line: "#d8e0ea",
        accent: "#2563eb",
        good: "#047857",
        warn: "#b45309",
        bad: "#b91c1c"
      }
    }
  },
  plugins: []
};

export default config;
