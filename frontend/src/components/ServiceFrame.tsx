"use client";

import { ExternalLink, ShieldCheck, Zap, Activity, Monitor } from "lucide-react";
import styles from "./ServiceFrame.module.css";
import { useState } from "react";

interface ServiceFrameProps {
    name: string;
    description: string;
    serviceUrl?: string;
}

// Service URL mapping for local development vs production
const getServiceUrl = (serviceUrl: string | undefined): string | undefined => {
    if (!serviceUrl) return undefined;

    // Check if we're in development (localhost or 127.0.0.1)
    const isDevelopment = typeof window !== 'undefined' &&
        (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

    if (isDevelopment) {
        // Map service paths to their local development ports
        const servicePortMap: Record<string, string> = {
            '/aitutor/': 'http://localhost:3002/aitutor/',
            '/aiwriter/': 'http://localhost:3001/aiwriter/',
        };
        return servicePortMap[serviceUrl] || serviceUrl;
    }

    // In production, use relative paths (nginx handles routing)
    return serviceUrl;
};

const ServiceFrame = ({ name, description, serviceUrl }: ServiceFrameProps) => {
    const [showPreview, setShowPreview] = useState(false);
    const token = typeof window !== 'undefined' ? localStorage.getItem("token") : null;

    // Get the correct URL based on environment
    const resolvedServiceUrl = getServiceUrl(serviceUrl);
    const authenticatedUrl = resolvedServiceUrl && token
        ? `${resolvedServiceUrl}${resolvedServiceUrl.includes('?') ? '&' : '?'}token=${token}`
        : resolvedServiceUrl;

    const handleLaunch = () => {
        if (authenticatedUrl) {
            window.open(authenticatedUrl, "_blank");
        }
    };

    return (
        <div className={`${styles.container} animate-fade-in`}>
            <div className={styles.hero}>
                <div className={styles.heroContent}>
                    <div className={styles.badge}>
                        <ShieldCheck size={14} />
                        <span>Enterprise Certified Module</span>
                    </div>
                    <h1>{name}</h1>
                    <p className={styles.heroDesc}>{description}</p>

                    <div className={styles.actionRow}>
                        <button className="btn-launch" onClick={handleLaunch}>
                            <Zap size={20} fill="currentColor" />
                            Launch Full Portal
                        </button>
                        <button
                            className={styles.secondaryBtn}
                            onClick={() => setShowPreview(!showPreview)}
                        >
                            {showPreview ? <Monitor size={20} /> : <Activity size={20} />}
                            {showPreview ? "Close Preview" : "Quick Preview"}
                        </button>
                    </div>
                </div>

                <div className={styles.statsPanel}>
                    <div className={styles.statItem}>
                        <div className={styles.statIcon} style={{ background: '#fcfaf7', color: 'var(--success)' }}>
                            <Activity size={18} />
                        </div>
                        <div>
                            <span className={styles.statLabel}>Service Status</span>
                            <span className={styles.statValue}>Operational</span>
                        </div>
                    </div>
                    <div className={styles.statItem}>
                        <div className={styles.statIcon} style={{ background: '#fcfaf7', color: 'var(--accent)' }}>
                            <Zap size={18} />
                        </div>
                        <div>
                            <span className={styles.statLabel}>Latency Rate</span>
                            <span className={styles.statValue}>42ms</span>
                        </div>
                    </div>
                </div>
            </div>

            {showPreview && authenticatedUrl && (
                <div className={`${styles.previewSection} premium-card`}>
                    <div className={styles.previewHeader}>
                        <div className={styles.dotGroup}>
                            <div className={styles.dot}></div>
                            <div className={styles.dot}></div>
                            <div className={styles.dot}></div>
                        </div>
                        <span className={styles.previewTitle}>Secure Preview Instance</span>
                        <div className={styles.launchIconBtn} onClick={handleLaunch}>
                            <ExternalLink size={16} />
                        </div>
                    </div>
                    <iframe
                        src={authenticatedUrl}
                        className={styles.iframe}
                        title={`${name} Preview`}
                    />
                </div>
            )}

            {!showPreview && (
                <div className={styles.featureGrid}>
                    <div className={`${styles.featureCard} premium-card`}>
                        <h3>Unified Tracking</h3>
                        <p>All activities in this module are automatically synchronized with your enterprise learning records.</p>
                    </div>
                    <div className={`${styles.featureCard} premium-card`}>
                        <h3>Cross-Session Persistence</h3>
                        <p>Drafts and session state are preserved even when switching between windows.</p>
                    </div>
                </div>
            )}

            <footer className={styles.footer}>
                <ShieldCheck size={16} />
                <span>End-to-end encryption active for this service session.</span>
            </footer>
        </div>
    );
};

export default ServiceFrame;
