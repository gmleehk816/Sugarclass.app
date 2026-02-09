"use client";

import AdminSidebar from "@/components/AdminSidebar";
import styles from "./AdminLayout.module.css";
import { usePathname } from "next/navigation";

export default function AdminLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    const pathname = usePathname();

    // Some fancy logic to update title based on path
    const getPageTitle = () => {
        if (pathname === "/admin") return "Admin Dashboard";
        if (pathname.includes("/aimaterials")) return "AI Materials Management";
        if (pathname.includes("/logs")) return "System Logs";
        if (pathname.includes("/users")) return "User Management";
        return "Administration";
    };

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
                <div className={styles.content}>
                    {children}
                </div>
            </main>
        </div>
    );
}
