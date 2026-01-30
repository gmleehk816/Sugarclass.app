"use client";

import { Flame } from "lucide-react";
import styles from "./StreakBadge.module.css";

interface StreakInfo {
    current_streak: number;
    longest_streak: number;
    last_activity_date: string | null;
}

interface StreakBadgeProps {
    streak: StreakInfo;
}

const StreakBadge = ({ streak }: StreakBadgeProps) => {
    const isActive = streak.current_streak > 0;

    return (
        <div className={styles.container}>
            <div className={`${styles.fireIcon} ${!isActive ? styles.fireIconInactive : ''}`}>
                <Flame size={24} />
            </div>
            <div className={styles.content}>
                <div className={`${styles.streakCount} ${!isActive ? styles.streakCountInactive : ''}`}>
                    {streak.current_streak} {streak.current_streak === 1 ? 'Day' : 'Days'}
                </div>
                <div className={`${styles.label} ${!isActive ? styles.labelInactive : ''}`}>
                    {isActive ? 'Current Streak' : 'Start your streak today!'}
                </div>
            </div>
            {streak.longest_streak > 0 && (
                <div className={styles.bestStreak}>
                    <div className={styles.bestLabel}>Best</div>
                    <div className={styles.bestValue}>{streak.longest_streak}</div>
                </div>
            )}
        </div>
    );
};

export default StreakBadge;
