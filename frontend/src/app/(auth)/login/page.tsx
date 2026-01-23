"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { GraduationCap, Mail, Lock, Loader2, ArrowRight, BookOpen, ShieldCheck, Zap } from "lucide-react";
import { auth } from "@/lib/api";
import styles from "../Auth.module.css";
import Image from "next/image";

export default function LoginPage() {
    const [email, setEmail] = useState("");
    const [password, setPassword] = useState("");
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState("");
    const router = useRouter();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError("");

        try {
            const result = await auth.login({ email, password });
            if (result.access_token) {
                localStorage.setItem("token", result.access_token);
                router.push("/dashboard");
            } else {
                throw new Error(result.detail || "Login failed");
            }
        } catch (err: any) {
            setError(err.message || "Invalid credentials. Access denied.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.page}>
            <div className={styles.authContainer}>
                {/* Visual Art Storytelling Section */}
                <div className={styles.artSection}>
                    <div className={styles.artContent}>
                        <Image
                            src="/study_art.png"
                            alt="Learning Abstract"
                            width={600}
                            height={600}
                            className={styles.mainIllustration}
                            priority
                        />
                        <div className={`${styles.floatingArtShape} ${styles.artShape1}`}>
                            <BookOpen size={24} />
                            <div>
                                <span style={{ display: 'block', fontWeight: 800, fontSize: '0.8rem' }}>SMART LEARNING</span>
                                <span style={{ display: 'block', fontSize: '0.7rem', opacity: 0.7 }}>Have fun learning!</span>
                            </div>
                        </div>
                        <div className={`${styles.floatingArtShape} ${styles.artShape2}`}>
                            <ShieldCheck size={24} />
                            <div>
                                <span style={{ display: 'block', fontWeight: 800, fontSize: '0.8rem' }}>SAFE & SECURE</span>
                                <span style={{ display: 'block', fontSize: '0.7rem', opacity: 0.7 }}>Trusted by Teachers</span>
                            </div>
                        </div>
                    </div>
                </div>

                {/* Authentication Panel */}
                <div className={styles.card}>
                    <div className={styles.header}>
                        <div className={styles.logo}>
                            <GraduationCap className={styles.logoIcon} size={54} />
                            <span className="gradient-text">Sugarclass</span>
                        </div>
                        <h1 className={styles.title}>Login</h1>
                        <p className={styles.subtitle}>Welcome to your fun learning world!</p>
                    </div>

                    <form className={styles.form} onSubmit={handleSubmit}>
                        {error && <div className={styles.error}>{error}</div>}

                        <div className={styles.inputGroup}>
                            <label htmlFor="email">My Email</label>
                            <div className={styles.inputWrapper}>
                                <Mail className={styles.inputIcon} size={24} />
                                <input
                                    id="email"
                                    type="email"
                                    placeholder="myname@email.com"
                                    value={email}
                                    onChange={(e) => setEmail(e.target.value)}
                                    required
                                    autoComplete="email"
                                />
                            </div>
                        </div>

                        <div className={styles.inputGroup}>
                            <label htmlFor="password">My Password</label>
                            <div className={styles.inputWrapper}>
                                <Lock className={styles.inputIcon} size={24} />
                                <input
                                    id="password"
                                    type="password"
                                    placeholder="••••••••"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    autoComplete="current-password"
                                />
                            </div>
                        </div>

                        <button
                            type="submit"
                            className={styles.submitBtn}
                            disabled={isLoading}
                        >
                            {isLoading ? (
                                <Loader2 className="spin" size={24} />
                            ) : (
                                <>
                                    <span>Let's Go!</span>
                                    <Zap size={20} fill="currentColor" />
                                </>
                            )}
                        </button>
                    </form>

                    <div className={styles.footer}>
                        Don't have an account?
                        <Link href="/register" className={styles.link}>
                            Sign Up Now
                        </Link>
                    </div>
                </div>
            </div>

            <div className="grid-pattern"></div>
        </div>
    );
}
