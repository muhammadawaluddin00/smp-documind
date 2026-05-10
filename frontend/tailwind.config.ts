import type { Config } from 'tailwindcss';

/**
 * SMP DocuMind brand tokens
 * -------------------------
 * Centralised here so a brand refresh is a one-file change. Update
 * these values to match SMP Technology's official palette when the
 * brand kit becomes available.
 */
const config: Config = {
  content: [
    './app/**/*.{ts,tsx}',
    './components/**/*.{ts,tsx}',
  ],
  theme: {
    extend: {
      colors: {
        // Primary palette — deep enterprise navy + electric teal
        ink: {
          50:  '#f4f7fb',
          100: '#e6edf6',
          200: '#c8d6e8',
          300: '#9eb5d3',
          500: '#456293',
          700: '#1f3554',
          900: '#0b1a30',
          950: '#06101f',
        },
        signal: {
          // Teal accent — used for KPIs, focus states, charts
          400: '#34d3c2',
          500: '#13b9a6',
          600: '#0e9789',
          700: '#0f7a72',
        },
        warn: { 500: '#f59e0b' },
        bad:  { 500: '#ef4444' },
        ok:   { 500: '#10b981' },
      },
      fontFamily: {
        // Distinctive, professional pairing — see BRAND_GUIDELINES.md
        display: ['"Plus Jakarta Sans"', 'system-ui', 'sans-serif'],
        body:    ['"Inter"', 'system-ui', 'sans-serif'],
        mono:    ['"JetBrains Mono"', 'ui-monospace', 'monospace'],
      },
      boxShadow: {
        soft: '0 1px 2px rgba(11,26,48,0.04), 0 4px 12px rgba(11,26,48,0.06)',
        glow: '0 0 0 4px rgba(19,185,166,0.15)',
      },
    },
  },
  plugins: [],
};

export default config;
