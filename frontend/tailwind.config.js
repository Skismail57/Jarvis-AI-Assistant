/** @type {import('tailwindcss').Config} */
export default {
  content: [
    "./index.html",
    "./src/**/*.{js,ts,jsx,tsx}",
  ],
  theme: {
    extend: {
      colors: {
        jarvis: {
          bg: '#05050a',
          bgLight: '#0a0a12',
          panel: '#121220',
          border: 'rgba(123,47,247,0.2)',
          text: '#ffffff',
          textDim: 'rgba(255,255,255,0.5)',
          pink: '#ff2e88',
          purple: '#7b2ff7',
          cyan: '#00eaff',
        },
      },
      backgroundImage: {
        'jarvis-gradient': 'linear-gradient(135deg, #ff2e88 0%, #7b2ff7 50%, #00eaff 100%)',
        'jarvis-gradient-soft': 'linear-gradient(135deg, rgba(255,46,136,0.1) 0%, rgba(123,47,247,0.1) 50%, rgba(0,234,255,0.1) 100%)',
      },
      boxShadow: {
        'neon-purple': '0 0 20px rgba(123,47,247,0.5)',
        'neon-pink': '0 0 20px rgba(255,46,136,0.5)',
        'neon-cyan': '0 0 20px rgba(0,234,255,0.5)',
        'glass': '0 8px 32px rgba(0,0,0,0.3)',
      },
      fontFamily: {
        sans: ['Inter', 'system-ui', 'sans-serif'],
        mono: ['JetBrains Mono', 'monospace'],
      },
      keyframes: {
        'pulse-glow': {
          '0%, 100%': { boxShadow: '0 0 20px rgba(123,47,247,0.5)' },
          '50%': { boxShadow: '0 0 40px rgba(123,47,247,0.8)' },
        },
        'float': {
          '0%, 100%': { transform: 'translateY(0px)' },
          '50%': { transform: 'translateY(-10px)' },
        },
        'shimmer': {
          '0%': { backgroundPosition: '-200% center' },
          '100%': { backgroundPosition: '200% center' },
        },
        'waveform-bar': {
          '0%, 100%': { height: '20%' },
          '50%': { height: '100%' },
        },
        'typing-dot': {
          '0%, 100%': { opacity: '0.3' },
          '50%': { opacity: '1' },
        },
        'gradient-shift': {
          '0%, 100%': { backgroundPosition: '0% 50%' },
          '50%': { backgroundPosition: '100% 50%' },
        },
        'spin-slow': {
          'from': { transform: 'rotate(0deg)' },
          'to': { transform: 'rotate(360deg)' },
        },
        'fade-in-up': {
          '0%': { opacity: '0', transform: 'translateY(20px)' },
          '100%': { opacity: '1', transform: 'translateY(0)' },
        },
        'pulse-ring': {
          '0%': { transform: 'scale(0.8)', opacity: '1' },
          '100%': { transform: 'scale(1.5)', opacity: '0' },
        },
        'fade-in': {
          '0%': { opacity: '0' },
          '100%': { opacity: '1' },
        },
        'slide-in': {
          '0%': { opacity: '0', transform: 'translateX(-10px)' },
          '100%': { opacity: '1', transform: 'translateX(0)' },
        },
      },
      animation: {
        'pulse-glow': 'pulse-glow 2s ease-in-out infinite',
        'float': 'float 3s ease-in-out infinite',
        'shimmer': 'shimmer 3s linear infinite',
        'waveform-bar': 'waveform-bar 1s ease-in-out infinite',
        'typing-dot': 'typing-dot 1.4s ease-in-out infinite',
        'gradient-shift': 'gradient-shift 8s ease infinite',
        'spin-slow': 'spin-slow 20s linear infinite',
        'fade-in-up': 'fade-in-up 0.5s ease-out',
        'pulse-ring': 'pulse-ring 1.5s ease-out infinite',
        'fade-in': 'fade-in 0.2s ease-out',
        'slide-in': 'slide-in 0.2s ease-out',
      },
    },
  },
  plugins: [],
}
