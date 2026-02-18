"use client";

import { useEffect, useState } from "react";
import { useRouter } from "next/navigation";
import { auth } from "@/lib/api";
import AdminSidebar from "@/components/AdminSidebar";
import styles from "./AdminLayout.module.css";
import { usePathname } from "next/navigation";
import { Loader2, ShieldAlert } from "lucide-react";

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();
    const router = useRouter();
    const [authState, setAuthState] = useState<"loading" | "authorized" | "denied">("loading");

    useEffect(() => {
        const checkAdmin = async () => {
            try {
                const token = localStorage.getItem("token");
                if (!token) {
                    setAuthState("denied");
                    return;
                }
                const user = await auth.me();
                if (user.is_superuser) {
                    setAuthState("authorized");
                } else {
                    setAuthState("denied");
                }
            } catch {
                setAuthState("denied");
            }
        };
        checkAdmin();
    }, []);

    useEffect(() => {
        if (authState === "denied") {
            router.replace("/dashboard");
        }
    }, [authState, router]);

    // Some fancy logic to update title based on path
    const getPageTitle = () => {
        if (pathname === "/admin") return "Admin Dashboard";
        if (pathname.includes("/aimaterials")) return "AI Materials Management";
        if (pathname.includes("/logs")) return "System Logs";
        if (pathname.includes("/users")) return "User Management";
        return "Administration";
    };

    if (authState === "loading") {
        return (
            <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: "100vh",
                background: "#fdfbf7",
                flexDirection: "column",
                gap: "16px",
            }}>
                <Loader2
                    size={40}
                    color="#927559"
                    style={{ animation: "spin 1s linear infinite" }}
                />
                <p style={{
                    color: "#64748b",
                    fontSize: "0.95rem",
                    fontWeight: 500,
                }}>
                    Verifying admin access...
                </p>
                <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
            </div>
        );
    }

    if (authState === "denied") {
        return (
            <div style={{
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                height: "100vh",
                background: "#fdfbf7",
                flexDirection: "column",
                gap: "16px",
            }}>
                <ShieldAlert size={48} color="#ef4444" />
                <p style={{
                    color: "#334155",
                    fontSize: "1.1rem",
                    fontWeight: 600,
                }}>
                    Access Denied
                </p>
                <p style={{ color: "#64748b", fontSize: "0.9rem" }}>
                    Redirecting to dashboard...
                </p>
            </div>
        );
    }

    return (
        <div className={styles.adminLayout}>
            <AdminSidebar />
            <main className={styles.main}>
                <header className={styles.header}>
                    <h1 className={styles.headerTitle}>{getPageTitle()}</h1>
                    <div className={styles.headerActions}>
                        {/* Add admin specific actions like user profile or notifications here */}
                    </div>
                </header>
                <div className={`${styles.content} ${pathname.startsWith('/admin/aimaterials') ? styles.contentFull : ''}`}>
                    {children}
                </div>
            </main>
        </div>
    );
}
