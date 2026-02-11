import React from 'react';
import { LucideIcon } from 'lucide-react';
import styles from './InsightCard.module.css';

interface InsightCardProps {
    title: string;
    value: string | number;
    label: string;
    icon: LucideIcon;
    color: string;
    trend?: {
        value: string;
        positive: boolean;
    };
}

const InsightCard: React.FC<InsightCardProps> = ({
    title,
    value,
    label,
    icon: Icon,
    color,
    trend
}) => {
    const bgStyle = {
        background: `${color}10`,
        color: color
    };

    return (
        <div className={styles.card}>
            <div className={styles.iconBox} style={bgStyle}>
                <Icon size={20} />
            </div>

            <div className={styles.content}>
                <span className={styles.title}>{title}</span>
                <div className={styles.valueRow}>
                    <span className={styles.value}>{value}</span>
                    {trend && (
                        <span className={`${styles.trend} ${trend.positive ? styles.positive : styles.negative}`}>
                            {trend.value}
                        </span>
                    )}
                </div>
                <span className={styles.label}>{label}</span>
            </div>
        </div>
    );
};

export default InsightCard;
