/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
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
