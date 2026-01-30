"use client";

import styles from "./ActivityChart.module.css";

interface DailyActivity {
    date: string;
    count: number;
}

interface ActivityChartProps {
    data: DailyActivity[];
    title?: string;
}

const ActivityChart = ({ data, title = "This Week" }: ActivityChartProps) => {
    const maxCount = Math.max(...data.map(d => d.count), 1);
    const dayNames = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    const getDayName = (dateStr: string) => {
        const date = new Date(dateStr);
        return dayNames[date.getDay()];
    };

    return (
        <div className={styles.container}>
            {title && <h4 className={styles.title}>{title}</h4>}
            <div className={styles.chart}>
                {data.map((day, index) => {
                    const heightPercent = maxCount > 0 ? (day.count / maxCount) * 100 : 0;
                    const isToday = index === data.length - 1;

                    return (
                        <div key={day.date} className={styles.barContainer}>
                            <div className={styles.barWrapper}>
                                <div
                                    className={`${styles.bar} ${isToday ? styles.barToday : ''}`}
                                    style={{ height: `${Math.max(heightPercent, 8)}%` }}
                                >
                                    {day.count > 0 && (
                                        <span className={styles.barValue}>{day.count}</span>
                                    )}
                                </div>
                            </div>
                            <span className={`${styles.dayLabel} ${isToday ? styles.dayLabelToday : ''}`}>
                                {getDayName(day.date)}
                            </span>
                        </div>
                    );
                })}
            </div>
        </div>
    );
};

export default ActivityChart;
