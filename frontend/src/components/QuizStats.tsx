"use client";

import { Trophy, Target, TrendingUp } from "lucide-react";
import styles from "./QuizStats.module.css";

interface QuizStatsProps {
    totalQuizzes: number;
    avgScore: number | null;
    bestScore: number | null;
}

const QuizStats = ({ totalQuizzes, avgScore, bestScore }: QuizStatsProps) => {
    if (totalQuizzes === 0) {
        return (
            <div className={styles.emptyState}>
                <Target size={32} className={styles.emptyIcon} />
                <p>Take your first quiz to see your stats!</p>
            </div>
        );
    }

    return (
        <div className={styles.container}>
            <div className={styles.statCard}>
                <div className={styles.iconWrapper} style={{ background: '#dbeafe', color: '#2563eb' }}>
                    <Target size={18} />
                </div>
                <div className={styles.statInfo}>
                    <span className={styles.statValue}>{totalQuizzes}</span>
                    <span className={styles.statLabel}>Quizzes Taken</span>
                </div>
            </div>

            <div className={styles.statCard}>
                <div className={styles.iconWrapper} style={{ background: '#dcfce7', color: '#16a34a' }}>
                    <TrendingUp size={18} />
                </div>
                <div className={styles.statInfo}>
                    <span className={styles.statValue}>
                        {avgScore !== null ? `${avgScore}%` : '-'}
                    </span>
                    <span className={styles.statLabel}>Average Score</span>
                </div>
            </div>

            <div className={styles.statCard}>
                <div className={styles.iconWrapper} style={{ background: '#fef3c7', color: '#d97706' }}>
                    <Trophy size={18} />
                </div>
                <div className={styles.statInfo}>
                    <span className={styles.statValue}>
                        {bestScore !== null ? `${bestScore}%` : '-'}
                    </span>
                    <span className={styles.statLabel}>Best Score</span>
                </div>
            </div>
        </div>
    );
};

export default QuizStats;
