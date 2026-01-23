"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { GraduationCap, Mail, Lock, User, Loader2, ArrowRight, ShieldCheck, Zap, Activity } from "lucide-react";
import { auth } from "@/lib/api";
import styles from "../Auth.module.css";
import Image from "next/image";

export default function RegisterPage() {
    const [name, setName] = useState("");
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
            await auth.register({ email, password, full_name: name });
            const loginResult = await auth.login({ email, password });
            if (loginResult.access_token) {
                localStorage.setItem("token", loginResult.access_token);
                router.push("/dashboard");
            }
        } catch (err: any) {
            setError(err.message || "Site provisioning failed.");
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className={styles.page}>
            <div className={styles.authContainer}>
                {/* Visual Art Storytelling Section */}
                <div className={styles.artSection} style={{ background: 'linear-gradient(135deg, rgba(74, 93, 78, 0.05), rgba(44, 62, 80, 0.05))' }}>
                    <div className={styles.artContent}>
                        <Image
                            src="/tech_art.png"
                            alt="Learning Abstract"
                            width={600}
                            height={600}
                            className={styles.mainIllustration}
                            priority
                        />
                        <div className={`${styles.floatingArtShape} ${styles.artShape1}`}>
                            <Activity size={24} />
                            <div>
                                <span style={{ display: 'block', fontWeight: 800, fontSize: '0.8rem' }}>GETTING READY</span>
                                <span style={{ display: 'block', fontSize: '0.7rem', opacity: 0.7 }}>Almost there!</span>
                            </div>
                        </div>
                        <div className={`${styles.floatingArtShape} ${styles.artShape2}`}>
                            <Zap size={24} fill="currentColor" />
                            <div>
                                <span style={{ display: 'block', fontWeight: 800, fontSize: '0.8rem' }}>FAST START</span>
                                <span style={{ display: 'block', fontSize: '0.7rem', opacity: 0.7 }}>Jump right in!</span>
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
                        <h1 className={styles.title}>Join Us</h1>
                        <p className={styles.subtitle}>Create your account and start the fun!</p>
                    </div>

                    <form className={styles.form} onSubmit={handleSubmit}>
                        {error && <div className={styles.error}>{error}</div>}

                        <div className={styles.inputGroup}>
                            <label htmlFor="name">My Full Name</label>
                            <div className={styles.inputWrapper}>
                                <User className={styles.inputIcon} size={24} />
                                <input
                                    id="name"
                                    type="text"
                                    placeholder="What is your name?"
                                    value={name}
                                    onChange={(e) => setName(e.target.value)}
                                    required
                                    autoComplete="name"
                                />
                            </div>
                        </div>

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
                            <label htmlFor="password">Create Password</label>
                            <div className={styles.inputWrapper}>
                                <Lock className={styles.inputIcon} size={24} />
                                <input
                                    id="password"
                                    type="password"
                                    placeholder="Min. 8 characters"
                                    value={password}
                                    onChange={(e) => setPassword(e.target.value)}
                                    required
                                    autoComplete="new-password"
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
                                    <span>Join Sugarclass!</span>
                                    <ArrowRight size={20} />
                                </>
                            )}
                        </button>
                    </form>

                    <div className={styles.footer}>
                        Already a member?
                        <Link href="/login" className={styles.link}>
                            Login Here
                        </Link>
                    </div>
                </div>
            </div>

            <div className="grid-pattern"></div>
        </div>
    );
}
