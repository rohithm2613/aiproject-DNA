/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  darkMode: 'class',
  theme: {
    extend: {
      colors: {
        dna: {
          bg: '#0B0F19',
          card: '#111827',
          surface: '#1A2234',
          border: '#232E47',
          hover: '#1F2B45',
          text: {
            primary: '#F3F4F6',
            secondary: '#9CA3AF',
            muted: '#6B7280'
          },
          accent: {
            purple: '#8B5CF6',
            electric: '#38BDF8',
            blue: '#3B82F6',
            violet: '#6D28D9'
          }
        }
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', '-apple-system', 'BlinkMacSystemFont', 'Segoe UI', 'Roboto', 'sans-serif'],
      },
      boxShadow: {
        'glow-purple': '0 0 20px -5px rgba(139, 92, 246, 0.25)',
        'glow-blue': '0 0 20px -5px rgba(56, 189, 248, 0.25)',
      }
    },
  },
  plugins: [],
}

