/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        brand: {
          darkest: '#090a0f',      // Deep space black
          dark: '#11131c',         // Card background slate-black
          card: '#1b1e2e',         // Brightened card hover state
          accent: '#6366f1',       // Electric Indigo
          accentLight: '#818cf8',  // Glowing Indigo
          emerald: '#10b981',      // Cyber Emerald
          rose: '#f43f5e'          // Coral Rose
        }
      },
      fontFamily: {
        sans: ['Outfit', 'Inter', 'system-ui', 'sans-serif'],
      }
    },
  },
  plugins: [],
}
