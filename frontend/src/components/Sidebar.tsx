"use client";

import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
    LayoutDashboard,
    BookOpen,
    PenTool,
    FileSearch,
    Settings,
    LogOut,
    GraduationCap
} from "lucide-react";
import styles from "./Sidebar.module.css";

const Sidebar = () => {
    const pathname = usePathname();
    const router = useRouter();

    const menuItems = [
        { name: "Home", icon: LayoutDashboard, path: "/dashboard" },
        { name: "AI Teacher", icon: BookOpen, path: "/services/tutor" },
        { name: "Writing Hub", icon: PenTool, path: "/services/writer" },
        { name: "Quiz Master", icon: FileSearch, path: "/services/examiner" },
        { name: "Settings", icon: Settings, path: "/settings" },
    ];

    const handleLogout = () => {
        localStorage.removeItem("token");
        router.push("/login");
    };

    return (
        <aside className={styles.sidebar}>
            <div className={styles.logo}>
                <GraduationCap className={styles.logoIcon} size={32} />
                <span>Sugarclass</span>
            </div>

            <nav className={styles.nav}>
                {menuItems.map((item) => {
                    const Icon = item.icon;
                    const isActive = pathname === item.path;
                    return (
                        <Link
                            key={item.path}
                            href={item.path}
                            className={`${styles.navItem} ${isActive ? styles.active : ""}`}
                        >
                            <Icon size={22} className={styles.icon} />
                            <span>{item.name}</span>
                        </Link>
                    );
                })}
            </nav>

            <div className={styles.footer}>
                <button onClick={handleLogout} className={styles.logoutBtn}>
                    <LogOut size={22} />
                    <span>Sign Out</span>
                </button>
            </div>
        </aside>
    );
};

export default Sidebar;
