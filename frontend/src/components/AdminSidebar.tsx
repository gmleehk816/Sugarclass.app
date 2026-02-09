"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import {
    LayoutDashboard,
    Library,
    BookOpen,
    PenTool,
    FileSearch,
    ChevronLeft,
    ChevronRight,
    LogOut,
    ShieldCheck,
    Menu,
    X,
    Server,
    Users,
    Settings
} from "lucide-react";
import styles from "./AdminSidebar.module.css";

const AdminSidebar = () => {
    const pathname = usePathname();
    const [isCollapsed, setIsCollapsed] = useState(false);
    const [isMobileMenuOpen, setIsMobileMenuOpen] = useState(false);

    const menuItems = [
        {
            group: "MAIN",
            items: [
                { name: "Admin Home", icon: LayoutDashboard, path: "/admin" },
                { name: "Site Logs", icon: Server, path: "/admin/logs" },
            ]
        },
        {
            group: "MICROSERVICES",
            items: [
                { name: "AI Materials", icon: Library, path: "/admin/aimaterials" },
                { name: "AI Teacher", icon: BookOpen, path: "/admin/tutor", status: "Coming Soon" },
                { name: "Writing Hub", icon: PenTool, path: "/admin/writer", status: "Coming Soon" },
                { name: "AI Examiner", icon: FileSearch, path: "/admin/examiner", status: "Coming Soon" },
            ]
        },
        {
            group: "AUTHENTICATION",
            items: [
                { name: "Users", icon: Users, path: "/admin/users" },
                { name: "Groups", icon: ShieldCheck, path: "/admin/groups" },
            ]
        }
    ];

    useEffect(() => {
        const handleResize = () => {
            setIsCollapsed(window.innerWidth < 1024);
        };
        handleResize();
        window.addEventListener('resize', handleResize);
        return () => window.removeEventListener('resize', handleResize);
    }, []);

    useEffect(() => {
        setIsMobileMenuOpen(false);
    }, [pathname]);

    return (
        <>
            {/* Mobile Header */}
            <header className={styles.mobileHeader}>
                <div className={styles.mobileLogo}>
                    <ShieldCheck className={styles.logoIcon} size={28} />
                    <span>Sugarclass Admin</span>
                </div>
                <button
                    className={styles.menuToggle}
                    onClick={() => setIsMobileMenuOpen(!isMobileMenuOpen)}
                >
                    {isMobileMenuOpen ? <X size={24} /> : <Menu size={24} />}
                </button>
            </header>

            {/* Admin Sidebar */}
            <aside className={`${styles.sidebar} ${isCollapsed ? styles.collapsed : ""} ${isMobileMenuOpen ? styles.mobileOpen : ""}`}>
                <div className={styles.logo}>
                    <ShieldCheck className={styles.logoIcon} size={32} />
                    <div className={`${styles.logoText} ${isCollapsed ? styles.hidden : ""}`}>
                        <span className={styles.brand}>Sugarclass</span>
                        <span className={styles.adminTag}>Administration</span>
                    </div>
                </div>

                <nav className={styles.nav}>
                    {menuItems.map((group, gIdx) => (
                        <div key={gIdx} className={styles.navGroup}>
                            {!isCollapsed && <label className={styles.groupLabel}>{group.group}</label>}
                            {group.items.map((item) => {
                                const Icon = item.icon;
                                const isActive = item.path === '/admin'
                                    ? pathname === item.path
                                    : pathname.startsWith(item.path);
                                const isComingSoon = item.status === "Coming Soon";

                                return (
                                    <Link
                                        key={item.path}
                                        href={isComingSoon ? "#" : item.path}
                                        className={`${styles.navItem} ${isActive ? styles.active : ""} ${isComingSoon ? styles.disabled : ""}`}
                                        title={isCollapsed ? `${item.name}${isComingSoon ? " (Coming Soon)" : ""}` : ""}
                                        onClick={(e) => isComingSoon && e.preventDefault()}
                                    >
                                        <Icon size={20} className={styles.navIcon} />
                                        <div className={`${styles.itemContent} ${isCollapsed ? styles.hidden : ""}`}>
                                            <span className={styles.itemName}>{item.name}</span>
                                            {isComingSoon && <span className={styles.badge}>Soon</span>}
                                        </div>
                                        {isActive && !isCollapsed && <div className={styles.activeIndicator} />}
                                    </Link>
                                );
                            })}
                        </div>
                    ))}
                </nav>

                <div className={styles.footer}>
                    <Link href="/dashboard" className={styles.exitBtn}>
                        <LogOut size={20} />
                        <span className={isCollapsed ? styles.hidden : ""}>Exit Admin</span>
                    </Link>

                    <button
                        className={styles.collapseBtn}
                        onClick={() => setIsCollapsed(!isCollapsed)}
                    >
                        {isCollapsed ? <ChevronRight size={18} /> : <ChevronLeft size={18} />}
                    </button>
                </div>
            </aside>

            {isMobileMenuOpen && (
                <div
                    className={styles.backdrop}
                    onClick={() => setIsMobileMenuOpen(false)}
                />
            )}
        </>
    );
};

export default AdminSidebar;
