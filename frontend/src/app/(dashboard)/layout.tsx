import Sidebar from "@/components/Sidebar";
import styles from "./DashboardLayout.module.css";

export default function DashboardLayout({
    children,
}: {
    children: React.ReactNode;
}) {
    return (
        <div className="dashboard-layout">
            <Sidebar />
            <main className={styles.main}>
                <div className="grid-pattern"></div>
                <div className="corner-glow"></div>
                <div className="main-content">
                    {children}
                </div>
            </main>
        </div>
    );
}
