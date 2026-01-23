"use client";

import { useState, useEffect } from "react";
import styles from "./Settings.module.css";
import {
    User,
    Lock,
    Bell,
    Globe,
    Shield,
    Save,
    Database,
    Link as LinkIcon
} from "lucide-react";
import { auth } from "@/lib/api";

const SettingsPage = () => {
    const [activeTab, setActiveTab] = useState("profile");
    const [user, setUser] = useState<any>(null);
    const [loading, setLoading] = useState(true);
    const [isSaving, setIsSaving] = useState(false);

    useEffect(() => {
        async function fetchUser() {
            try {
                const userData = await auth.me();
                setUser(userData);
            } catch (err) {
                console.error("Failed to fetch user", err);
            } finally {
                setLoading(false);
            }
        }
        fetchUser();
    }, []);

    const tabs = [
        { id: "profile", label: "Profile", icon: User },
        { id: "security", label: "Security", icon: Lock },
        { id: "services", label: "External Services", icon: LinkIcon },
        { id: "preferences", label: "Preferences", icon: Globe },
    ];

    if (loading) return <div className="animate-fade-in">Loading Settings...</div>;

    return (
        <div className={styles.container}>
            <header className={styles.header}>
                <h1 className={styles.title}>Settings</h1>
                <p className={styles.subtitle}>Manage your account, preferences, and service integrations.</p>
            </header>

            <div className={styles.contentLayout}>
                <aside className={styles.tabList}>
                    {tabs.map((tab) => {
                        const Icon = tab.icon;
                        return (
                            <button
                                key={tab.id}
                                className={`${styles.tabBtn} ${activeTab === tab.id ? styles.activeTab : ""}`}
                                onClick={() => setActiveTab(tab.id)}
                            >
                                <Icon size={18} />
                                <span>{tab.label}</span>
                            </button>
                        );
                    })}
                </aside>

                <main className={`${styles.tabContent} premium-card`}>
                    {activeTab === "profile" && (
                        <section className={styles.section}>
                            <h2>Profile Information</h2>
                            <div className={styles.formGrid}>
                                <div className={styles.inputGroup}>
                                    <label>Full Name</label>
                                    <input type="text" defaultValue={user?.full_name} placeholder="John Doe" />
                                </div>
                                <div className={styles.inputGroup}>
                                    <label>Email Address</label>
                                    <input type="email" defaultValue={user?.email} disabled />
                                    <p className={styles.inputHint}>Email cannot be changed directly for security.</p>
                                </div>
                                <div className={styles.inputGroup}>
                                    <label>Bio</label>
                                    <textarea placeholder="Tell us about your learning goals..." rows={4} />
                                </div>
                            </div>
                        </section>
                    )}

                    {activeTab === "security" && (
                        <section className={styles.section}>
                            <h2>Security Settings</h2>
                            <div className={styles.formGrid}>
                                <div className={styles.inputGroup}>
                                    <label>Current Password</label>
                                    <input type="password" placeholder="••••••••" />
                                </div>
                                <div className={styles.inputGroup}>
                                    <label>New Password</label>
                                    <input type="password" placeholder="••••••••" />
                                </div>
                                <div className={styles.inputGroup}>
                                    <label>Confirm New Password</label>
                                    <input type="password" placeholder="••••••••" />
                                </div>
                            </div>
                            <div className={styles.infoBox}>
                                <Shield size={18} />
                                <p>Two-factor authentication is currently disabled. Enable it to add an extra layer of security to your account.</p>
                            </div>
                        </section>
                    )}

                    {activeTab === "services" && (
                        <section className={styles.section}>
                            <h2>Service Integrations</h2>
                            <p className={styles.sectionHint}>Manage the connection URLs for your AI Tutor, Writer, and Examiner services.</p>
                            <div className={styles.formGrid}>
                                <div className={styles.inputGroup}>
                                    <label>AI Tutor Endpoint</label>
                                    <input type="url" defaultValue="http://localhost:8001" />
                                </div>
                                <div className={styles.inputGroup}>
                                    <label>AI Writer Endpoint</label>
                                    <input type="url" defaultValue="http://localhost:8002" />
                                </div>
                                <div className={styles.inputGroup}>
                                    <label>AI Examiner Endpoint</label>
                                    <input type="url" defaultValue="http://localhost:8003" />
                                </div>
                            </div>
                            <div className={styles.infoBox}>
                                <Database size={18} />
                                <p>These endpoints are used for server-side communication and background activity tracking.</p>
                            </div>
                        </section>
                    )}

                    {activeTab === "preferences" && (
                        <section className={styles.section}>
                            <h2>User Preferences</h2>
                            <div className={styles.formGrid}>
                                <div className={styles.inputGroup}>
                                    <label>Interface Language</label>
                                    <select>
                                        <option>English (US)</option>
                                        <option>Bengali</option>
                                        <option>Spanish</option>
                                    </select>
                                </div>
                                <div className={styles.inputGroup}>
                                    <label>Email Notifications</label>
                                    <div className={styles.toggleRow}>
                                        <span>Weekly progress reports</span>
                                        <input type="checkbox" defaultChecked />
                                    </div>
                                    <div className={styles.toggleRow}>
                                        <span>Service announcements</span>
                                        <input type="checkbox" defaultChecked />
                                    </div>
                                </div>
                            </div>
                        </section>
                    )}

                    <footer className={styles.tabFooter}>
                        <button
                            className={styles.saveBtn}
                            onClick={() => {
                                setIsSaving(true);
                                setTimeout(() => setIsSaving(false), 1000);
                            }}
                            disabled={isSaving}
                        >
                            <Save size={18} />
                            <span>{isSaving ? "Saving..." : "Save Changes"}</span>
                        </button>
                    </footer>
                </main>
            </div>
        </div>
    );
};

export default SettingsPage;
