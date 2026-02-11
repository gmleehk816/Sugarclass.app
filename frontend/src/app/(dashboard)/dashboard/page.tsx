"use client";

import { useEffect, useState } from "react";
import styles from "./Dashboard.module.css";
import HeroSection from "@/components/HeroSection";
import AdminHub from "@/components/AdminHub";
import ShortcutCard from "@/components/ShortcutCard";
import InsightCard from "@/components/InsightCard";
import StreakBadge from "@/components/StreakBadge";
import {
    BookOpen,
    PenTool,
    ShieldCheck,
    Library,
    Clock,
    Zap,
    TrendingUp,
    Calendar,
    ChevronRight,
    Sparkles,
    GraduationCap,
    Globe,
    FileText,
    CheckCircle
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
    const isAdmin = user?.is_superuser;

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

    const getServiceIcon = (service: string) => {
        switch (service) {
            case 'writer': return <PenTool size={18} />;
            case 'examiner': return <ShieldCheck size={18} />;
            case 'aimaterials': return <Library size={18} />;
            default: return <BookOpen size={18} />;
        }
    };

    const getServiceColor = (service: string) => {
        switch (service) {
            case 'writer': return { bg: '#fef3c7', color: '#d97706' };
            case 'examiner': return { bg: '#dcfce7', color: '#16a34a' };
            case 'aimaterials': return { bg: '#f3e8ff', color: '#7e22ce' };
            default: return { bg: '#e0f2fe', color: '#0284c7' };
        }
    };

    // Creative Insights logic
    const topFocus = summary.service_breakdown.reduce((prev: any, current: any) =>
        (prev.count > current.count) ? prev : current, { service: 'None', count: 0 }
    );

    return (
        <div className={`${styles.container} animate-fade-in`}>
            {/* Hero Section */}
            <HeroSection
                firstName={firstName}
                streak={summary.streak.current_streak}
                totalActivities={summary.total_activities}
                todayActivities={summary.today_activities}
            />

            {/* Insights Row */}
            <div className={styles.insightsGrid}>
                <InsightCard
                    title="Questions Solved"
                    value={summary.total_questions || 0}
                    label="Knowledge Validations"
                    icon={CheckCircle}
                    color="#16a34a"
                    trend={{ value: "+12% this week", positive: true }}
                />
                <InsightCard
                    title="Articles Written"
                    value={summary.total_articles || 0}
                    label="Drafts & Essays"
                    icon={FileText}
                    color="#d97706"
                />
                <InsightCard
                    title="Tutor Sessions"
                    value={summary.tutor_sessions || 0}
                    label="Active Learning"
                    icon={GraduationCap}
                    color="#0284c7"
                />
                <InsightCard
                    title="Subject Versatility"
                    value={summary.unique_subjects || 0}
                    label="Disciplines Mastered"
                    icon={Globe}
                    color="#7e22ce"
                />
            </div>

            {/* Admin Hub - Only for Superusers */}
            {isAdmin && <AdminHub />}

            <div className={styles.mainGrid}>
                {/* Left Column: Shortcuts */}
                <div className={styles.shortcutsColumn}>
                    <div className={styles.sectionHeader}>
                        <h2>My Learning Apps</h2>
                    </div>

                    <div className={styles.shortcutList}>
                        <ShortcutCard
                            title="My AI Teacher"
                            description="Personalized 1-on-1 tutoring on any subject."
                            icon={GraduationCap}
                            href="/services/tutor"
                            variant="primary"
                        />
                        <ShortcutCard
                            title="AI Writing Hub"
                            description="AI-powered assistant for essays and stories."
                            icon={PenTool}
                            href="/services/writer"
                            variant="secondary"
                        />
                        <ShortcutCard
                            title="Quiz Master"
                            description="Interactive quizzes to test your knowledge."
                            icon={ShieldCheck}
                            href="/services/examiner"
                            variant="accent"
                        />
                        <ShortcutCard
                            title="AI Materials"
                            description="Browse subjects and lessons curated by AI."
                            icon={Library}
                            href="/services/materials"
                            variant="primary"
                            color="#7e22ce"
                        />
                    </div>
                </div>

                {/* Right Column: Activity Sneak Peak */}
                <aside className={styles.sidebarColumn}>
                    <div className={styles.sectionHeader}>
                        <h2>Recent Activity</h2>
                        <Link href="/history" className={styles.seeAll}>
                            All <ChevronRight size={14} />
                        </Link>
                    </div>

                    <div className={styles.activityFeed}>
                        {summary.recent_history.length > 0 ? (
                            summary.recent_history.slice(0, 6).map((activity: any) => {
                                const colors = getServiceColor(activity.service);
                                return (
                                    <div key={activity.id} className={styles.feedItem}>
                                        <div className={styles.feedIcon} style={{
                                            background: colors.bg,
                                            color: colors.color
                                        }}>
                                            {getServiceIcon(activity.service)}
                                        </div>
                                        <div className={styles.feedContent}>
                                            <span className={styles.feedTitle}>{formatActivityType(activity)}</span>
                                            <span className={styles.feedTime}>
                                                {new Date(activity.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                            </span>
                                        </div>
                                        {activity.score !== null && (
                                            <span className={styles.feedScore}>{activity.score}%</span>
                                        )}
                                    </div>
                                );
                            })
                        ) : (
                            <div className={styles.emptyFeed}>
                                <Clock size={24} />
                                <p>No recent activity. Let's start learning!</p>
                            </div>
                        )}
                    </div>

                    {/* Learning Focus Widget - Creative Addition */}
                    <div className={styles.focusWidget}>
                        <div className={styles.focusHeader}>
                            <Zap size={16} />
                            <span>Learning Focus</span>
                        </div>
                        <div className={styles.focusContent}>
                            <div className={styles.focusIcon} style={getServiceColor(topFocus.service)}>
                                {getServiceIcon(topFocus.service)}
                            </div>
                            <div className={styles.focusInfo}>
                                <h3>{topFocus.service.charAt(0).toUpperCase() + topFocus.service.slice(1)}</h3>
                                <p>Your primary AI partner</p>
                            </div>
                        </div>
                        <div className={styles.focusBarBg}>
                            <div
                                className={styles.focusBarFill}
                                style={{
                                    width: `${Math.min(100, (topFocus.count / summary.total_activities) * 100)}%`,
                                    background: getServiceColor(topFocus.service).color
                                }}
                            />
                        </div>
                        <p className={styles.focusQuote}>
                            {topFocus.service === 'writer' && "Your storytelling is reaching new heights!"}
                            {topFocus.service === 'examiner' && "You're a knowledge-testing machine!"}
                            {topFocus.service === 'tutor' && "Your curiousity is your greatest strength."}
                            {topFocus.service === 'aimaterials' && "You're building a massive knowledge base."}
                            {topFocus.service === 'None' && "Start your journey with any AI app!"}
                        </p>
                    </div>

                    {/* Streak & Tips */}
                    <div className={styles.extraWidgets}>
                        <div className={styles.streakWidget}>
                            <StreakBadge streak={summary.streak} />
                        </div>
                        <div className={styles.tipWidget}>
                            <div className={styles.tipHeader}>
                                <Sparkles size={16} />
                                <span>Pro Tip</span>
                            </div>
                            <p>
                                {summary.streak.current_streak > 3
                                    ? "Unstoppable! Reaching a 7-day streak unlocks a special achievement."
                                    : "Keep it up! 15 minutes of learning a day keeps the knowledge growing."}
                            </p>
                        </div>
                    </div>
                </aside>
            </div>
        </div>
    );
};

export default DashboardPage;
