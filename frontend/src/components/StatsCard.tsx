import styles from "./StatsCard.module.css";
import { LucideIcon } from "lucide-react";

interface StatsCardProps {
    title: string;
    value: string | number;
    icon: LucideIcon;
    color: string;
}

const StatsCard = ({ title, value, icon: Icon, color }: StatsCardProps) => {
    return (
        <div className={`glass ${styles.card}`} style={{ "--accent-color": color } as any}>
            <div className={styles.iconWrapper}>
                <Icon size={24} />
            </div>
            <div className={styles.content}>
                <p className={styles.title}>{title}</p>
                <h3 className={styles.value}>{value}</h3>
            </div>
        </div>
    );
};

export default StatsCard;
