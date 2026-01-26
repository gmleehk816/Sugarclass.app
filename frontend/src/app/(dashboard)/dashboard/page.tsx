"use client";

import { useEffect, useState } from "react";
import styles from "./Dashboard.module.css";
import StatsCard from "@/components/StatsCard";
import {
    BookOpen,
    PenTool,
    Activity,
    ArrowRight,
    Zap,
    LayoutGrid,
    Clock,
    UserCheck,
    GraduationCap,
    ShieldCheck,
    ChevronRight,
    Sparkles
} from "lucide-react";
import Link from "next/link";
import { progress, auth } from "@/lib/api";

const DashboardPage = () => {
    const [summary, setSummary] = useState<any>(null);
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchData() {
            try {
                const [summaryData, userData] = await Promise.all([
                    progress.getSummary(),
                    auth.me()
                ]);
                setSummary(summaryData);
                setUser(userData);
            } catch (err) {
                console.error("Dashboard fetch error", err);
            } finally {
                setLoading(false);
            }
        }
        fetchData();
    }, []);

    if (loading) return <div className="loading">Getting your workspace ready...</div>;
    if (!summary) return <div className="loading">Oops! We couldn't connect. Try again.</div>;

    const firstName = user?.full_name?.split(' ')[0] || 'Friend';

    return (
        <div className={`${styles.container} animate-fade-in`}>
            {/* Header with Friendly Accents */}
            <header className={styles.header}>
                <div>
                    <h1 className={styles.title}>Welcome back, <span className="gradient-text">{firstName}</span>!</h1>
                    <p className={styles.subtitle}>Your smart learning space. You are doing a great job today!</p>
                </div>
                <div className={styles.headerAccents}>
                    <div className="animate-float">
                        <Sparkles size={32} color="var(--accent)" />
                    </div>
                </div>
            </header>

            {/* Fun Stats */}
            <section className={styles.statsGrid}>
                <StatsCard
                    title="My Learning Apps"
                    value="3 Apps"
                    icon={LayoutGrid}
                    color="var(--primary)"
                />
                <StatsCard
                    title="My Progress"
                    value={`${Math.min(100, summary.total_activities * 12)}%`}
                    icon={Activity}
                    color="#e67e22"
                />
                <StatsCard
                    title="Star Badges"
                    value="0 Earned"
                    icon={UserCheck}
                    color="var(--accent)"
                />
                <StatsCard
                    title="Learning Power"
                    value="100%"
                    icon={Zap}
                    color="#f1c40f"
                />
            </section>

            {/* 3-Column Compact Content Grid */}
            <div className={styles.contentGrid}>
                {/* Column 1: Recent Work */}
                <section className={styles.recentActivity}>
                    <div className={styles.sectionHeader}>
                        <h2>My Recent Work</h2>
                        <Link href="/history" className={styles.seeAll}>
                            See All <ChevronRight size={14} />
                        </Link>
                    </div>

                    <div className={`${styles.activityCard} premium-card`}>
                        <div className={styles.activityList}>
                            {summary.recent_history.length > 0 ? (
                                summary.recent_history.map((activity: any) => (
                                    <div key={activity.id} className={styles.activityItem}>
                                        <div className={styles.activityIcon} style={{
                                            background: activity.service === 'writer' ? '#fcf9f5' : '#f5f8fc',
                                            color: activity.service === 'writer' ? 'var(--accent)' : 'var(--primary)'
                                        }}>
                                            {activity.service === 'writer' ? <PenTool size={18} /> : <BookOpen size={18} />}
                                        </div>
                                        <div className={styles.activityInfo}>
                                            <span className={styles.activityName}>
                                                {activity.service === 'writer' ? 'AI Stories' : 'AI Lesson'}
                                            </span>
                                            <span className={styles.activityTime}>
                                                {new Date(activity.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                        <Sparkles size={14} color="#f1c40f" opacity={0.6} />
                                    </div>
                                ))
                            ) : (
                                <div style={{ textAlign: 'center', padding: '40px 0', opacity: 0.5 }}>
                                    <Clock size={24} style={{ margin: '0 auto 12px' }} />
                                    <p style={{ fontSize: '0.85rem' }}>Start learning to see your work here!</p>
                                </div>
                            )}
                        </div>
                    </div>
                </section>

                {/* Column 2: My Learning Apps */}
                <section className={styles.quickLaunch}>
                    <div className={styles.sectionHeader}>
                        <h2>Learning Apps</h2>
                    </div>
                    <Link href="/services/tutor" className={`${styles.launchCard} premium-card`}>
                        <div className={`${styles.launchIconSquare} ${styles.tutorIcon}`}>
                            <GraduationCap size={22} />
                        </div>
                        <div className={styles.launchText}>
                            <h3>My AI Teacher</h3>
                            <p>Ask anything and learn something new today!</p>
                        </div>
                    </Link>

                    <Link href="/services/writer" className={`${styles.launchCard} premium-card`}>
                        <div className={`${styles.launchIconSquare} ${styles.writerIcon}`}>
                            <PenTool size={22} />
                        </div>
                        <div className={styles.launchText}>
                            <h3>AI Writing Hub</h3>
                            <p>Write amazing stories and essays with AI help.</p>
                        </div>
                    </Link>

                    <Link href="/services/examiner" className={`${styles.launchCard} premium-card`}>
                        <div className={`${styles.launchIconSquare}`} style={{ background: '#f0fff4', color: '#27ae60' }}>
                            <ShieldCheck size={22} />
                        </div>
                        <div className={styles.launchText}>
                            <h3>Quiz Master</h3>
                            <p>Test your knowledge and earn star badges!</p>
                        </div>
                    </Link>
                </section>

                {/* Column 3: Fun Tips */}
                <section className={styles.insightsColumn}>
                    <div className={styles.sectionHeader}>
                        <h2>Smart Tips</h2>
                    </div>

                    <div className={styles.insights}>
                        <div className={styles.insightsDecoration}></div>
                        <div className={styles.insightCard}>
                            <p><strong>Did you know?</strong> Writing every day helps you become a master storyteller. Keep up the great work!</p>
                        </div>
                        <div style={{ marginTop: 'auto', display: 'flex', alignItems: 'center', gap: '8px', fontSize: '0.8rem', opacity: 0.8 }}>
                            <ShieldCheck size={14} />
                            <span>Your data is safe and private.</span>
                        </div>
                    </div>
                </section>
            </div>

        </div>
    );
};

export default DashboardPage;
