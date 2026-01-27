"use client";

import { useEffect, useState } from "react";
import styles from "./page.module.css";

export default function ExaminerPage() {
    const [authenticatedUrl, setAuthenticatedUrl] = useState<string | null>(null);

    useEffect(() => {
        const token = localStorage.getItem("token");
        const isDevelopment = typeof window !== 'undefined' &&
            (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1');

        let baseUrl = "/examiner/";
        if (isDevelopment) {
            baseUrl = "http://localhost:3403/examiner/";
        }

        if (token) {
            const url = `${baseUrl}${baseUrl.includes('?') ? '&' : '?'}token=${token}`;
            setAuthenticatedUrl(url);
        } else {
            setAuthenticatedUrl(baseUrl);
        }
    }, []);

    return (
        <div className={styles.microserviceContainer}>
            {authenticatedUrl && (
                <iframe
                    src={authenticatedUrl}
                    className={styles.microserviceIframe}
                    title="AI Examiner"
                    allow="fullscreen"
                    sandbox="allow-scripts allow-same-origin allow-forms allow-popups allow-modals allow-downloads"
                />
            )}
        </div>
    );
}
