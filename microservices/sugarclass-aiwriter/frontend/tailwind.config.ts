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
                // Primary Colors - Soft Teal/Turquoise for kids
                'primary': '#0D9488',  // Soft teal (kid-friendly)
                'primary-dark': '#0F766E',  // Darker teal
                'accent': '#06B6D4',  // Bright cyan
                'accent-light': '#22D3EE',  // Light cyan
                'success': '#10B981',  // Green
                'warning': '#F59E0B',  // Warm orange

                // Neutral Colors - Warm Off-White/Beige (kept the same)
                'background': '#FAF8F5',  // Warm off-white
                'surface': '#FEFDFB',  // Very light beige
                'surface-dark': '#F5F1EB',  // Light tan
                'surface-darker': '#EBE6DF',  // Medium tan
                'border': '#E0D9CF',  // Warm gray
                'border-light': '#EDE8E1',  // Light warm gray
                'text-primary': '#1C1917',  // Warm black
                'text-secondary': '#57534E',  // Medium brown-gray
                'text-muted': '#78716C',  // Light brown-gray
                'text-light': '#A8A29E',  // Very light brown-gray

                // Category Colors - Bright and playful
                'science': '#8B5CF6',  // Purple
                'tech': '#3B82F6',  // Blue
                'environment': '#10B981',  // Green
                'sports': '#F97316',  // Orange
                'arts': '#EC4899',  // Pink
                'health': '#EF4444',  // Red

                // Legacy compatibility
                'sky-blue': '#0D9488',
                'ocean': '#0F766E',
                'mint': '#10B981',
                'amber': '#F59E0B',
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
            lineHeight: {
                'relaxed': '1.75',
            },
            animation: {
                'bounce-slow': 'bounce 3s ease-in-out infinite',
                'pulse-slow': 'pulse 3s ease-in-out infinite',
            },
        },
    },
    plugins: [],
}

export default config
