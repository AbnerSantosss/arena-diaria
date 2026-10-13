/** Tailwind v3 compilado (sem CDN). Gerar com:
 *  npx tailwindcss@3.4.17 -c build/tailwind.config.js -i build/tailwind.src.css -o assets/css/tailwind.css --minify
 */
module.exports = {
  content: ['./*.html', './assets/js/*.js'],
  theme: {
    extend: {
      fontFamily: {
        sans: ['Inter', '-apple-system', 'BlinkMacSystemFont', '"Segoe UI"', 'Roboto', 'sans-serif'],
      },
      colors: {
        navy: { DEFAULT: '#0B132B', 2: '#1C2541' },
      },
    },
  },
  plugins: [],
};
