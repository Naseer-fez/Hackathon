/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        apple: {
          blue: "#0071E3",
          mint: "#30D158",
          amber: "#FF9F0A",
          red: "#FF453A",
          indigo: "#5E5CE6",
          bg: "#08090a",
          glass: "rgba(255, 255, 255, 0.04)",
          glassDark: "rgba(0, 0, 0, 0.4)",
        },
        bis: {
          navy: "#0a192f",
          blue: "#1e3a8a",
          amber: "#d97706",
          emerald: "#059669",
          slate: "#0f172a",
          card: "#1e293b",
          border: "#334155",
        }
      }
    },
  },
  plugins: [],
}
