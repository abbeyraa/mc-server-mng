import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        mc: {
          green: "#5BAD53",
          dark: "#1A1A1A",
          panel: "#2A2A2A",
          border: "#3A3A3A",
        },
      },
    },
  },
  plugins: [require("@tailwindcss/forms")],
};

export default config;
