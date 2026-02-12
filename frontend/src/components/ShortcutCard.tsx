import React from 'react';
import Link from 'next/link';
import { LucideIcon, ArrowRight } from 'lucide-react';
import styles from './ShortcutCard.module.css';

interface ShortcutCardProps {
    title: string;
    description: string;
    icon: LucideIcon;
    href: string;
    color?: string;
    status?: string;
    variant?: 'primary' | 'secondary' | 'accent' | 'admin';
}

const ShortcutCard: React.FC<ShortcutCardProps> = ({
    title,
    description,
    icon: Icon,
    href,
    color,
    status,
    variant = 'primary'
}) => {
    const isComingSoon = status === 'Coming Soon';

    return (
        <Link
            href={isComingSoon ? '#' : href}
            className={`${styles.card} ${styles[variant]} ${isComingSoon ? styles.disabled : ''}`}
            onClick={(e) => isComingSoon && e.preventDefault()}
        >
            <div className={styles.iconWrapper} style={color ? { backgroundColor: `${color}15`, color: color } : {}}>
                <Icon size={24} />
            </div>

            <div className={styles.content}>
                <div className={styles.header}>
                    <h3 className={styles.title}>{title}</h3>
                    {status && <span className={styles.badge}>{status}</span>}
                </div>
                <p className={styles.description}>{description}</p>
            </div>

            {!isComingSoon && (
                <div className={styles.arrow}>
                    <ArrowRight size={20} />
                </div>
            )}
        </Link>
    );
};

export default ShortcutCard;
