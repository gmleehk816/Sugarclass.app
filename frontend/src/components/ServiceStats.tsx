"use client";

import { BookOpen, PenTool, ShieldCheck, Clock } from "lucide-react";
import styles from "./ServiceStats.module.css";

interface ServiceBreakdown {
    service: string;
    count: number;
    last_used: string | null;
    avg_score: number | null;
}

interface ServiceStatsProps {
    services: ServiceBreakdown[];
}

const serviceConfig: Record<string, { name: string; icon: any; color: string; bgColor: string }> = {
    tutor: {
        name: "AI Teacher",
        icon: BookOpen,
        color: "#0284c7",
        bgColor: "#e0f2fe"
    },
    writer: {
        name: "Writing Hub",
        icon: PenTool,
        color: "#d97706",
        bgColor: "#fef3c7"
    },
    examiner: {
        name: "Quiz Master",
        icon: ShieldCheck,
        color: "#16a34a",
        bgColor: "#dcfce7"
    }
};

const ServiceStats = ({ services }: ServiceStatsProps) => {
    const formatLastUsed = (dateStr: string | null) => {
        if (!dateStr) return "Not used yet";

        const date = new Date(dateStr);
        const now = new Date();
        const diffMs = now.getTime() - date.getTime();
        const diffMins = Math.floor(diffMs / 60000);
        const diffHours = Math.floor(diffMs / 3600000);
        const diffDays = Math.floor(diffMs / 86400000);

        if (diffMins < 1) return "Just now";
        if (diffMins < 60) return `${diffMins}m ago`;
        if (diffHours < 24) return `${diffHours}h ago`;
        if (diffDays === 1) return "Yesterday";
        if (diffDays < 7) return `${diffDays}d ago`;
        return date.toLocaleDateString();
    };

    return (
        <div className={styles.container}>
            {services.map((service) => {
                const config = serviceConfig[service.service] || {
                    name: service.service,
                    icon: BookOpen,
                    color: "#64748b",
                    bgColor: "#f1f5f9"
                };
                const Icon = config.icon;

                return (
                    <div key={service.service} className={styles.serviceCard}>
                        <div
                            className={styles.iconWrapper}
                            style={{ backgroundColor: config.bgColor, color: config.color }}
                        >
                            <Icon size={20} />
                        </div>
                        <div className={styles.info}>
                            <div className={styles.serviceName}>{config.name}</div>
                            <div className={styles.stats}>
                                <span className={styles.count}>{service.count} sessions</span>
                                {service.avg_score !== null && (
                                    <span className={styles.score}>
                                        Avg: {service.avg_score}%
                                    </span>
                                )}
                            </div>
                        </div>
                        <div className={styles.lastUsed}>
                            <Clock size={12} />
                            <span>{formatLastUsed(service.last_used)}</span>
                        </div>
                    </div>
                );
            })}
        </div>
    );
};

export default ServiceStats;
