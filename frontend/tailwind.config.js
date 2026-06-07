/** @type {import('tailwindcss').Config} */
export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      colors: {
        dark: {
          bg: '#0a0a0f',
          surface: '#111118',
          border: '#1e1e2e',
          hover: '#1a1a2e',
        },
        priority: {
          high: '#ff4444',
          medium: '#ff8c00',
          low: '#3b82f6',
          none: '#6b7280',
        },
        accent: '#00d4aa',
        text: {
          primary: '#e2e8f0',
          muted: '#64748b',
        },
      },
      fontFamily: {
        mono: ['JetBrains Mono', 'monospace'],
        sans: ['Inter', 'system-ui', 'sans-serif'],
      },
    },
  },
  plugins: [],
};
