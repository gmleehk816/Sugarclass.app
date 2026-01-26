import Link from 'next/link';
import { GraduationCap } from 'lucide-react';

export default function Navbar() {
    return (
        <nav className="sticky top-0 z-50 w-full bg-background/80 backdrop-blur-md border-b border-card-border">
            <div className="container mx-auto flex h-20 items-center justify-between px-6 md:px-10">
                <div className="flex items-center gap-3">
                    <div className="h-10 w-10 rounded-xl bg-primary flex items-center justify-center text-white">
                        <GraduationCap size={24} />
                    </div>
                    <span className="text-xl font-extrabold tracking-tight text-primary">
                        Quiz Master <span className="text-accent font-medium text-sm ml-1 opacity-80">by Sugarclass</span>
                    </span>
                </div>
                <div className="hidden md:flex items-center gap-8">
                    <Link href="/" className="text-sm font-semibold text-primary hover:text-accent transition-colors">
                        Exercises
                    </Link>
                    <Link href="/history" className="text-sm font-semibold text-slate-400 hover:text-primary transition-colors">
                        Rankings
                    </Link>
                    <Link href="/materials" className="text-sm font-semibold text-slate-400 hover:text-primary transition-colors">
                        Materials
                    </Link>
                </div>
                <div className="flex items-center gap-4">
                    <button className="px-6 py-2.5 rounded-xl bg-primary text-white text-sm font-bold hover:bg-primary-light transition-all shadow-md active:scale-95">
                        New Quiz
                    </button>
                </div>
            </div>
        </nav>
    );
}
