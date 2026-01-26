"use client";

import { useEffect, useState } from "react";
import styles from "./History.module.css";
import {
    Clock,
    BookOpen,
    PenTool,
    FileSearch,
    ChevronLeft,
    Calendar,
    ArrowUpRight
} from "lucide-react";
import Link from "next/link";
import { progress } from "@/lib/api";

const HistoryPage = () => {
    const [history, setHistory] = useState<any[]>([]);
    const [loading, setLoading] = useState(true);

    useEffect(() => {
        async function fetchHistory() {
            try {
                const data = await progress.getFullHistory(50);
                setHistory(data);
            } catch (err) {
                console.error("History fetch error", err);
            } finally {
                setLoading(false);
            }
        }
        fetchHistory();
    }, []);

    const getServiceIcon = (service: string) => {
        switch (service) {
            case 'writer': return <PenTool size={18} />;
            case 'tutor': return <BookOpen size={18} />;
            case 'examiner': return <FileSearch size={18} />;
            default: return <Clock size={18} />;
        }
    };

    const getServiceDetails = (service: string) => {
        switch (service) {
            case 'writer': return { label: 'AI Writing Hub', color: 'var(--accent)', bg: 'var(--accent-muted)' };
            case 'tutor': return { label: 'AI Teacher', color: 'var(--primary)', bg: 'var(--primary-muted)' };
            case 'examiner': return { label: 'Quiz Master', color: '#27ae60', bg: '#f0fff4' };
            default: return { label: 'Learning App', color: '#64748b', bg: '#f1f5f9' };
        }
    };

    if (loading) return <div className="loading">Retracing your steps...</div>;

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <div>
                    <Link href="/dashboard" className="back-link mb-4 inline-flex items-center gap-2 text-sm font-bold text-slate-500 hover:text-slate-800 transition-colors">
                        <ChevronLeft size={16} /> Back to My Hub
                    </Link>
                    <h1 className={styles.title}>My Learning <span className="gradient-text">History</span></h1>
                    <p className={styles.subtitle}>A complete look at everything you've learned and created.</p>
                </div>
            </header>

            <div className={styles.historyCard}>
                {history.length > 0 ? (
                    <div className={styles.tableContainer}>
                        <table className={styles.table}>
                            <thead>
                                <tr>
                                    <th>Activity</th>
                                    <th>Learning App</th>
                                    <th>Date & Time</th>
                                    <th></th>
                                </tr>
                            </thead>
                            <tbody>
                                {history.map((item) => {
                                    const details = getServiceDetails(item.service);
                                    const date = new Date(item.timestamp);
                                    return (
                                        <tr key={item.id} className={styles.row}>
                                            <td>
                                                <div className={styles.activityInfo}>
                                                    <span className={styles.activityName}>{item.activity_type || "Learning Session"}</span>
                                                    <span className={styles.activityDesc}>Completed a smart module</span>
                                                </div>
                                            </td>
                                            <td>
                                                <span className={styles.serviceBadge} style={{ background: details.bg, color: details.color }}>
                                                    {getServiceIcon(item.service)}
                                                    {details.label}
                                                </span>
                                            </td>
                                            <td>
                                                <div className="flex items-center gap-3 text-slate-500">
                                                    <Calendar size={14} />
                                                    <span className={styles.timestamp}>
                                                        {date.toLocaleDateString()} at {date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                                                    </span>
                                                </div>
                                            </td>
                                            <td>
                                                <Link href={`/services/${item.service}`} className="p-2 rounded-full hover:bg-slate-100 transition-colors inline-block">
                                                    <ArrowUpRight size={18} className="text-slate-400" />
                                                </Link>
                                            </td>
                                        </tr>
                                    );
                                })}
                            </tbody>
                        </table>
                    </div>
                ) : (
                    <div className={styles.empty}>
                        <Clock size={48} />
                        <h3>No history yet!</h3>
                        <p>Start a lesson or write a story to see it here.</p>
                        <Link href="/dashboard" className="btn-launch mt-6 inline-block">
                            Go to Dashboard
                        </Link>
                    </div>
                )}
            </div>
        </div>
    );
};

export default HistoryPage;
