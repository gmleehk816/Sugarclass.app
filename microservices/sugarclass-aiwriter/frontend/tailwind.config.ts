import type { Config } from 'tailwindcss'

const config: Config = {
    content: [
        './pages/**/*.{js,ts,jsx,tsx,mdx}',
        './components/**/*.{js,ts,jsx,tsx,mdx}',
        './app/**/*.{js,ts,jsx,tsx,mdx}',
    ],
    theme: {
        extend: {
            colors: {
                // Main Orchestrator App Colors - Slate & Ivory
                'primary': '#1e293b',       // Slate 800
                'primary-light': '#334155', // Slate 700
                'primary-muted': 'rgba(30, 41, 59, 0.05)',

                'accent': '#927559',        // Bronze Refined (main accent)
                'accent-light': '#a48c73',  // Light bronze
                'accent-muted': 'rgba(146, 117, 89, 0.1)',

                'success': '#3d5a45',       // Forest Sage
                'warning': '#b45309',
                'error': '#991b1b',

                // Neutral Colors - Warm Ivory/Beige
                'background': '#fcfaf7',    // Warm ivory
                'surface': 'rgba(255, 255, 255, 0.85)',
                'surface-dark': '#f5f1eb',
                'surface-darker': '#ebe6df',
                'border': 'rgba(0, 0, 0, 0.04)',
                'border-light': 'rgba(0, 0, 0, 0.08)',

                'text-primary': '#1a1a1b',
                'text-secondary': '#57534e',
                'text-muted': '#78716c',
                'text-light': '#a8a29e',

                // Category Colors - Muted to match overall theme
                'science': '#8B5CF6',
                'tech': '#3B82F6',
                'environment': '#10B981',
                'sports': '#F97316',
                'arts': '#EC4899',
                'health': '#EF4444',

                // Legacy compatibility
                'sky-blue': '#927559',      // Now matches accent
                'ocean': '#1e293b',         // Now matches primary
                'mint': '#10B981',
                'amber': '#b45309',
                'coral': '#F97316',
                'ai-purple': '#8B5CF6',
                'ai-purple-light': '#F3E8FF',
            },
            fontFamily: {
                sans: ['Outfit', 'sans-serif'],
                heading: ['Outfit', 'sans-serif'],
                body: ['Outfit', 'sans-serif'],
                mono: ['JetBrains Mono', 'Fira Code', 'monospace'],
            },
            borderRadius: {
                'xl': '32px',
                'lg': '24px',
                'md': '16px',
                'sm': '8px',
            },
            boxShadow: {
                'sm': '0 2px 4px rgba(0, 0, 0, 0.02)',
                'md': '0 10px 25px -5px rgba(0, 0, 0, 0.04), 0 8px 10px -6px rgba(0, 0, 0, 0.02)',
                'lg': '0 20px 50px -12px rgba(0, 0, 0, 0.08)',
                'glass': '0 8px 32px 0 rgba(31, 38, 135, 0.05)',
                'glow': '0 0 20px rgba(146, 117, 89, 0.2)',
            },
            transitionTimingFunction: {
                'smooth': 'cubic-bezier(0.16, 1, 0.3, 1)',
            },
            transitionDuration: {
                '400': '600ms',
            },
        },
    },
    plugins: [],
}

export default config
