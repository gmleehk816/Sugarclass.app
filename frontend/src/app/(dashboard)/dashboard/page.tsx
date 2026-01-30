"use client";

import { useEffect, useState } from "react";
import styles from "./Dashboard.module.css";
import StatsCard from "@/components/StatsCard";
import ActivityChart from "@/components/ActivityChart";
import StreakBadge from "@/components/StreakBadge";
import ServiceStats from "@/components/ServiceStats";
import QuizStats from "@/components/QuizStats";
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
    Sparkles,
    Calendar,
    TrendingUp
} from "lucide-react";
import Link from "next/link";
import { progress, auth } from "@/lib/api";

interface DailyActivity {
    date: string;
    count: number;
}

interface ServiceBreakdown {
    service: string;
    count: number;
    last_used: string | null;
    avg_score: number | null;
}

interface StreakInfo {
    current_streak: number;
    longest_streak: number;
    last_activity_date: string | null;
}

interface DashboardSummary {
    total_activities: number;
    last_activity: any;
    service_stats: Record<string, number>;
    service_breakdown: ServiceBreakdown[];
    activity_types: any[];
    today_activities: number;
    this_week_activities: number;
    this_month_activities: number;
    daily_activity: DailyActivity[];
    streak: StreakInfo;
    total_quizzes: number;
    avg_quiz_score: number | null;
    best_quiz_score: number | null;
    recent_history: any[];
}

const DashboardPage = () => {
    const [summary, setSummary] = useState<DashboardSummary | null>(null);
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

    // Format activity type for display
    const formatActivityType = (activity: any) => {
        const typeMap: Record<string, string> = {
            'chat_interaction': 'AI Chat',
            'document_created': 'Document Created',
            'exam_completed': 'Quiz Completed',
            'lesson_started': 'Lesson Started',
            'writing_session': 'Writing Session'
        };
        return typeMap[activity.activity_type] || activity.activity_type;
    };

    // Get icon for service
    const getServiceIcon = (service: string) => {
        switch (service) {
            case 'writer': return <PenTool size={18} />;
            case 'examiner': return <ShieldCheck size={18} />;
            default: return <BookOpen size={18} />;
        }
    };

    // Get color for service
    const getServiceColor = (service: string) => {
        switch (service) {
            case 'writer': return { bg: '#fef3c7', color: '#d97706' };
            case 'examiner': return { bg: '#dcfce7', color: '#16a34a' };
            default: return { bg: '#e0f2fe', color: '#0284c7' };
        }
    };

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

            {/* Quick Stats Row */}
            <section className={styles.statsGrid}>
                <StatsCard
                    title="Today's Activities"
                    value={summary.today_activities}
                    icon={Calendar}
                    color="var(--primary)"
                />
                <StatsCard
                    title="This Week"
                    value={summary.this_week_activities}
                    icon={TrendingUp}
                    color="#e67e22"
                />
                <StatsCard
                    title="Total Sessions"
                    value={summary.total_activities}
                    icon={Activity}
                    color="var(--accent)"
                />
                <StatsCard
                    title="Learning Power"
                    value={`${Math.min(100, summary.total_activities * 5 + summary.streak.current_streak * 10)}%`}
                    icon={Zap}
                    color="#f1c40f"
                />
            </section>

            {/* Main Content Grid */}
            <div className={styles.contentGrid}>
                {/* Column 1: Activity Overview */}
                <section className={styles.activityOverview}>
                    <div className={styles.sectionHeader}>
                        <h2>Activity Overview</h2>
                    </div>

                    {/* Streak Badge */}
                    <div className={styles.streakSection}>
                        <StreakBadge streak={summary.streak} />
                    </div>

                    {/* Weekly Activity Chart */}
                    <div className={`${styles.chartCard} premium-card`}>
                        <ActivityChart data={summary.daily_activity} title="Weekly Activity" />
                    </div>

                    {/* Quiz Performance */}
                    <div className={styles.quizSection}>
                        <h3 className={styles.subSectionTitle}>Quiz Performance</h3>
                        <QuizStats
                            totalQuizzes={summary.total_quizzes}
                            avgScore={summary.avg_quiz_score}
                            bestScore={summary.best_quiz_score}
                        />
                    </div>
                </section>

                {/* Column 2: Recent Activity & Services */}
                <section className={styles.middleColumn}>
                    <div className={styles.sectionHeader}>
                        <h2>Recent Activity</h2>
                        <Link href="/history" className={styles.seeAll}>
                            See All <ChevronRight size={14} />
                        </Link>
                    </div>

                    <div className={`${styles.activityCard} premium-card`}>
                        <div className={styles.activityList}>
                            {summary.recent_history.length > 0 ? (
                                summary.recent_history.slice(0, 5).map((activity: any) => {
                                    const colors = getServiceColor(activity.service);
                                    return (
                                        <div key={activity.id} className={styles.activityItem}>
                                            <div className={styles.activityIcon} style={{
                                                background: colors.bg,
                                                color: colors.color
                                            }}>
                                                {getServiceIcon(activity.service)}
                                            </div>
                                            <div className={styles.activityInfo}>
                                                <span className={styles.activityName}>
                                                    {formatActivityType(activity)}
                                                </span>
                                                <span className={styles.activityMeta}>
                                                    {activity.score !== null && (
                                                        <span className={styles.activityScore}>
                                                            Score: {activity.score}%
                                                        </span>
                                                    )}
                                                    <span className={styles.activityTime}>
                                                        {new Date(activity.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </span>
                                            </div>
                                        </div>
                                    );
                                })
                            ) : (
                                <div className={styles.emptyActivity}>
                                    <Clock size={24} />
                                    <p>Start learning to see your activity here!</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Service Usage */}
                    <div className={styles.serviceSection}>
                        <h3 className={styles.subSectionTitle}>Service Usage</h3>
                        <ServiceStats services={summary.service_breakdown} />
                    </div>
                </section>

                {/* Column 3: Quick Launch */}
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
                        <ArrowRight size={18} className={styles.launchArrow} />
                    </Link>

                    <Link href="/services/writer" className={`${styles.launchCard} premium-card`}>
                        <div className={`${styles.launchIconSquare} ${styles.writerIcon}`}>
                            <PenTool size={22} />
                        </div>
                        <div className={styles.launchText}>
                            <h3>AI Writing Hub</h3>
                            <p>Write amazing stories and essays with AI help.</p>
                        </div>
                        <ArrowRight size={18} className={styles.launchArrow} />
                    </Link>

                    <Link href="/services/examiner" className={`${styles.launchCard} premium-card`}>
                        <div className={`${styles.launchIconSquare}`} style={{ background: '#dcfce7', color: '#16a34a' }}>
                            <ShieldCheck size={22} />
                        </div>
                        <div className={styles.launchText}>
                            <h3>Quiz Master</h3>
                            <p>Test your knowledge and earn achievements!</p>
                        </div>
                        <ArrowRight size={18} className={styles.launchArrow} />
                    </Link>

                    {/* Tips Card */}
                    <div className={styles.tipsCard}>
                        <div className={styles.tipsHeader}>
                            <Sparkles size={16} />
                            <span>Pro Tip</span>
                        </div>
                        <p>
                            {summary.streak.current_streak > 0
                                ? `Great job! You're on a ${summary.streak.current_streak}-day streak. Keep it going!`
                                : "Start a learning streak by using any app today!"}
                        </p>
                    </div>
                </section>
            </div>
        </div>
    );
};

export default DashboardPage;
