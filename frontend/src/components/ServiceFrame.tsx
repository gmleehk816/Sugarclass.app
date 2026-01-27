"use client";

import { ArrowLeft, Activity, ShieldCheck } from "lucide-react";
import styles from "./ServiceFrame.module.css";
import { useRouter } from "next/navigation";
import { useEffect, useState } from "react";

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
            '/aitutor/': 'http://localhost:3402/aitutor/',
            '/aiwriter/': 'http://localhost:3401/aiwriter/',
            '/examiner/': 'http://localhost:3403/',
        };
        return servicePortMap[serviceUrl] || serviceUrl;
    }

    // In production, use relative paths (nginx handles routing)
    return serviceUrl;
};

const ServiceFrame = ({ name, description, serviceUrl }: ServiceFrameProps) => {
    const router = useRouter();
    const [authenticatedUrl, setAuthenticatedUrl] = useState<string | null>(null);
    const [isCollapsed, setIsCollapsed] = useState(false);

    useEffect(() => {
        // Auto-collapse on iPad (collapses to icons only)
        const handleResize = () => {
            setIsCollapsed(window.innerWidth < 1024);
        };

        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        // Set URL after client-side hydration to avoid mismatch
        const token = localStorage.getItem("token");
        const resolvedServiceUrl = getServiceUrl(serviceUrl);

        if (resolvedServiceUrl && token) {
            const url = `${resolvedServiceUrl}${resolvedServiceUrl.includes('?') ? '&' : '?'}token=${token}`;
            setAuthenticatedUrl(url);
        } else {
            setAuthenticatedUrl(resolvedServiceUrl || null);
        }
    }, [serviceUrl]);

    const handleGoBack = () => {
        router.push('/dashboard');
    };

    // Show loading state while hydrating
    if (!authenticatedUrl) {
        return (
            <div className={styles.loadingState}>
                <ShieldCheck size={48} />
                <p>Loading service...</p>
            </div>
        );
    }

    return (
        <div className={styles.fullscreenContainer}>
            {/* Sidebar Navigation */}
            <div className={`${styles.serviceSidebar} ${isCollapsed ? styles.collapsed : ''}`}>
                <button className={styles.backButton} onClick={handleGoBack} title="Back to Dashboard">
                    <ArrowLeft size={20} />
                    {!isCollapsed && <span>Back</span>}
                </button>

                <div className={styles.sidebarContent}>
                    {!isCollapsed && (
                        <>
                            <h3>{name}</h3>
                            <p>{description}</p>
                        </>
                    )}
                </div>

                <div className={styles.statusIndicators}>
                    <div className={styles.statusBadge}>
                        <Activity size={14} />
                        {!isCollapsed && <span>Live</span>}
                    </div>
                </div>
            </div>

            {/* Full-Screen Iframe */}
            <div className={styles.iframeWrapper}>
                {authenticatedUrl && (
                    <iframe
                        src={authenticatedUrl}
                        className={styles.fullscreenIframe}
                        title={name}
                        allow="fullscreen"
                        sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads"
                    />
                )}
            </div>
        </div>
    );
};

export default ServiceFrame;