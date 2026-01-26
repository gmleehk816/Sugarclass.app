"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname, useRouter } from "next/navigation";
import {
    LayoutDashboard,
    BookOpen,
    PenTool,
    FileSearch,
    Settings,
    LogOut,
    GraduationCap,
    ChevronLeft,
    ChevronRight,
    Menu,
    X
} from "lucide-react";
import styles from "./Sidebar.module.css";

const Sidebar = () => {
    const pathname = usePathname();
    const router = useRouter();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const menuItems = [
        { name: "Dashboard", icon: LayoutDashboard, path: "/dashboard" },
        { name: "AI Teacher", icon: BookOpen, path: "/services/tutor" },
        { name: "Writing Hub", icon: PenTool, path: "/services/writer" },
        { name: "Quiz Master", icon: FileSearch, path: "/services/examiner" },
        { name: "Settings", icon: Settings, path: "/settings" },
    ];

    const handleLogout = () => {
        localStorage.removeItem("token");
        router.push("/login");
    };

    // Close mobile menu on route change
    useEffect(() => {
        setIsMobileMenuOpen(false);
    }, [pathname]);

    return (
        <>
            {/* Mobile Header */}
            <header className={styles.mobileHeader}>
                <div className={styles.mobileLogo}>
                    <GraduationCap className={styles.logoIcon} size={28} />
                    <span>Sugarclass</span>
                </div>
                <button
                    className={styles.menuToggle}
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                >
                    {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </header>

            {/* Desktop/iPad Sidebar */}
            <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ""} ${isMobileMenuOpen ? styles.mobileOpen : ""}`}>
                <div className={styles.logo}>
                    <GraduationCap className={styles.logoIcon} size={32} />
                    <span className={isCollapsed ? styles.hidden : ""}>Sugarclass</span>
                </div>

                <nav className={styles.nav}>
                    {menuItems.map((item) => {
                        const Icon = item.icon;
                        const isActive = item.path === '/dashboard'
                            ? pathname === item.path
                            : pathname.startsWith(item.path);

                        return (
                            <Link
                                key={item.path}
                                href={item.path}
                                className={`${styles.navItem} ${isActive ? styles.active : ""}`}
                                title={isCollapsed ? item.name : ""}
                            >
                                <Icon size={22} className={styles.navIcon} />
                                <span className={isCollapsed ? styles.hidden : ""}>{item.name}</span>
                                {isActive && !isCollapsed && <div className={styles.activeIndicator} />}
                            </Link>
                        );
                    })}
                </nav>

                <div className={styles.footer}>
                    <button onClick={handleLogout} className={styles.logoutBtn}>
                        <LogOut size={22} />
                        <span className={isCollapsed ? styles.hidden : ""}>Sign Out</span>
                    </button>

                    <button
                        className={styles.collapseBtn}
                        onClick={() => setIsCollapsed(!isCollapsed)}
                    >
                        {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                    </button>
                </div>
            </aside>

            {/* Backdrop for mobile */}
            {isMobileMenuOpen && (
                <div
                    className={styles.backdrop}
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}
        </>
    );
};

export default Sidebar;
