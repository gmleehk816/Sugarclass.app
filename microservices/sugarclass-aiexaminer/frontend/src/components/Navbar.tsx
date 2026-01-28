'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { GraduationCap } from 'lucide-react';

export default function Navbar() {
    const pathname = usePathname();

    // Debug: log pathname to console
    if (typeof window !== 'undefined') {
        console.log('Current pathname:', pathname);
    }

    const isActive = (path: string) => {
        if (!pathname) return false;

        // Strip trailing slashes for consistent comparison
        const normalizedPathname = pathname.replace(/\/$/, '') || '/';
        const normalizedPath = path.replace(/\/$/, '') || '/';

        if (normalizedPath === '/') {
            return normalizedPathname === '/' || normalizedPathname.includes('/quiz');
        }

        return normalizedPathname.startsWith(normalizedPath);
    };

    return (
        <nav className="sticky top-0 z-50 w-full bg-background/80 backdrop-blur-md border-b border-card-border">
            <div className="container mx-auto flex h-20 items-center justify-between px-6 md:px-10">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center text-white">
                        <GraduationCap size={24} />
                    </div>
                    <span className="text-xl font-extrabold tracking-tight text-primary cursor-pointer" onClick={() => (window.location.href = '/')}>
                        AI Examiner <span className="text-accent font-medium text-sm ml-1 opacity-80">by Sugarclass</span>
                    </span>
                </div>
                <div className="hidden md:flex items-center gap-8">
                    <Link
                        href="/"
                        className={`text-sm font-semibold transition-colors ${isActive('/')
                            ? 'text-primary'
                            : 'text-slate-400 hover:text-primary'
                            }`}
                    >
                        Exercises
                    </Link>
                    <Link
                        href="/materials"
                        className={`text-sm font-semibold transition-colors ${isActive('/materials')
                            ? 'text-primary'
                            : 'text-slate-400 hover:text-primary'
                            }`}
                    >
                        Materials
                    </Link>
                    <Link
                        href="/rankings"
                        className={`text-sm font-semibold transition-colors ${isActive('/rankings')
                            ? 'text-primary'
                            : 'text-slate-400 hover:text-primary'
                            }`}
                    >
                        Rankings
                    </Link>
                </div>
                <div className="flex items-center gap-4">
                    <Link
                        href="/materials"
                        className="px-6 py-2.5 rounded-xl bg-primary text-white text-sm font-bold hover:bg-primary-light transition-all shadow-md active:scale-95"
                    >
                        New Quiz
                    </Link>
                </div>
            </div>
        </nav>
    );
}
