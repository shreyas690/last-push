/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        background: '#040d1a',
        surface: '#0a192f',
        hackerGreen: '#00ff66',
        cyberCyan: '#00f3ff',
        cyberRed: '#ff0055',
        primary: '#00ff66',
        primaryDark: '#00cc52',
        accent: '#00f3ff',
        danger: '#ff0055',
        textMain: '#e6f1ff',
        textMuted: '#8892b0'
      },
      fontFamily: {
        sans: ['Inter', 'sans-serif'],
        mono: ['Fira Code', 'JetBrains Mono', 'monospace']
      },
      backgroundImage: {
        'glass-gradient': 'linear-gradient(135deg, rgba(0, 255, 102, 0.05) 0%, rgba(0, 243, 255, 0.02) 100%)',
        'hacker-grid': 'linear-gradient(to right, rgba(0, 255, 102, 0.05) 1px, transparent 1px), linear-gradient(to bottom, rgba(0, 255, 102, 0.05) 1px, transparent 1px)'
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.5)',
        'neon-green': '0 0 15px rgba(0, 255, 102, 0.3)',
        'neon-cyan': '0 0 15px rgba(0, 243, 255, 0.3)',
        'neon-red': '0 0 15px rgba(255, 0, 85, 0.3)'
      }
    },
  },
  plugins: [],
}
