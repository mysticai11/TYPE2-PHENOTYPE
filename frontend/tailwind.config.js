/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        void: '#0A0A0C',
        panel: 'rgba(20, 22, 28, 0.6)',
        glass: 'rgba(255, 255, 255, 0.08)',
        muted: '#8B92A5',
        primary: '#F3F4F6',
        ai: {
          indigo: '#4F46E5',
          sapphire: '#3B82F6',
          glow: 'rgba(79, 70, 229, 0.5)'
        },
        zone: {
          healthy: '#10B981',
          ir: '#F59E0B',
          steatosis: '#3b82f6', // Cobalt
          dual: '#9F1239' // Crimson
        }
      },
      fontFamily: {
        sans: ['"Instrument Sans"', 'ui-sans-serif', 'system-ui', 'sans-serif'],
        mono: ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
        serif: ['"DM Serif Display"', 'ui-serif', 'serif']
      },
      boxShadow: {
        'glass': '0 4px 30px rgba(0, 0, 0, 0.5)',
        'glow': '0 0 15px rgba(79, 70, 229, 0.5)'
      },
      backdropBlur: {
        'md': '12px',
        'lg': '24px'
      },
      animation: {
        'pulse-slow': 'pulse-slow 2s cubic-bezier(0.4, 0, 0.6, 1) infinite',
        'bounce-once': 'bounce-once 0.6s cubic-bezier(0.175, 0.885, 0.32, 1.275) forwards',
        'fade-in': 'fade-in 0.3s ease-out forwards',
        'slide-down': 'slide-down 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
        'slide-left': 'slide-left 0.4s cubic-bezier(0.16, 1, 0.3, 1) forwards',
      },
      keyframes: {
        'pulse-slow': {
          '0%, 100%': { opacity: '0.4', transform: 'scale(0.95)' },
          '50%': { opacity: '1', transform: 'scale(1.05)' },
        },
        'bounce-once': {
          '0%': { transform: 'translateY(-200px)', opacity: '0' },
          '70%': { transform: 'translateY(10px)', opacity: '1' },
          '85%': { transform: 'translateY(-5px)' },
          '100%': { transform: 'translateY(0)' }
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' }
        },
        'slide-down': {
          '0%': { transform: 'translateY(-100%)' },
          '100%': { transform: 'translateY(0)' }
        },
        'slide-left': {
          '0%': { transform: 'translateX(100%)' },
          '100%': { transform: 'translateX(0)' }
        }
      }
    },
  },
  plugins: [],
}
