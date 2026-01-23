'use client'

import { motion } from 'framer-motion'
import { Loader2 } from 'lucide-react'

interface LoadingSpinnerProps {
    size?: 'sm' | 'md' | 'lg'
    message?: string
}

export default function LoadingSpinner({ size = 'md', message }: LoadingSpinnerProps) {
    const sizeClasses = {
        sm: 'w-6 h-6',
        md: 'w-12 h-12',
        lg: 'w-16 h-16'
    }

    const textSizeClasses = {
        sm: 'text-sm',
        md: 'text-base',
        lg: 'text-lg'
    }

    return (
        <div className="flex flex-col items-center justify-center gap-4">
            <motion.div
                animate={{ rotate: 360 }}
                transition={{ duration: 1, repeat: Infinity, ease: 'linear' }}
                className={`${sizeClasses[size]} border-4 border-primary border-t-transparent rounded-full`}
            />
            {message && (
                <p className={`${textSizeClasses[size]} text-text-secondary`}>{message}</p>
            )}
        </div>
    )
}

export function InlineLoadingSpinner() {
    return (
        <Loader2 className="w-4 h-4 animate-spin" />
    )
}
