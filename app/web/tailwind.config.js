const { keyframes } = require("framer-motion");

module.exports = {
    content: [
    "./app/**/*.{js,ts,jsx,tsx}",
    "./components/**/*.{js,ts,jsx,tsx}",
    "./pages/**/*.{js,ts,jsx,tsx}",
  ],
  purge: [],
  darkMode: false, // or 'media' or 'class'
  theme: {
    extend: {
        fontFamily:{
            customFont: ['"Poppins"', 'sans-serif'],
        },
    },
  },
  variants: {
    extend: {},
  },
  plugins: [],
}
