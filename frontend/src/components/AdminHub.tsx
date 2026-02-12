import React from 'react';
import {
    Library,
    Users,
    Server,
    ShieldCheck,
    Settings,
    FileText,
    Database,
    Zap
} from 'lucide-react';
import ShortcutCard from './ShortcutCard';
import styles from './AdminHub.module.css';

const AdminHub: React.FC = () => {
    return (
        <section className={styles.adminSection}>
            <div className={styles.sectionHeader}>
                <div className={styles.titleGroup}>
                    <ShieldCheck className={styles.headerIcon} size={24} />
                    <h2 className={styles.sectionTitle}>Command Center</h2>
                </div>
                <span className={styles.adminBadge}>Administrator Access</span>
            </div>

            <div className={styles.shortcutGrid}>
                <ShortcutCard
                    title="AI Materials"
                    description="Ingest textbooks, manage subjects, and curate AI-ready content."
                    icon={Library}
                    href="/admin/aimaterials"
                    variant="admin"
                />
                <ShortcutCard
                    title="User Management"
                    description="Manage school accounts, user roles, and student progress."
                    icon={Users}
                    href="/admin/users"
                    variant="admin"
                    status="Coming Soon"
                />
                <ShortcutCard
                    title="System Logs"
                    description="Real-time monitoring of microservices and system events."
                    icon={Server}
                    href="/admin/logs"
                    variant="admin"
                />
                <ShortcutCard
                    title="Global Config"
                    description="Manage API keys, system prompts, and global settings."
                    icon={Settings}
                    href="/admin/settings"
                    variant="admin"
                    status="Coming Soon"
                />
            </div>

            <div className={styles.quickInfoRow}>
                <div className={styles.infoCard}>
                    <Zap size={18} className={styles.infoIcon} />
                    <div className={styles.infoText}>
                        <span className={styles.infoLabel}>System Uptime</span>
                        <span className={styles.infoValue}>99.99%</span>
                    </div>
                </div>
                <div className={styles.infoCard}>
                    <Database size={18} className={styles.infoIcon} />
                    <div className={styles.infoText}>
                        <span className={styles.infoLabel}>Subjects Ingested</span>
                        <span className={styles.infoValue}>13 Active</span>
                    </div>
                </div>
                <div className={styles.infoCard}>
                    <FileText size={18} className={styles.infoIcon} />
                    <div className={styles.infoText}>
                        <span className={styles.infoLabel}>Pending Requests</span>
                        <span className={styles.infoValue}>0</span>
                    </div>
                </div>
            </div>
        </section>
    );
};

export default AdminHub;
