"use client";

import { useEffect, useState } from "react";
import styles from "./HeroSection.module.css";
import { Sparkles, Flame } from "lucide-react";

interface HeroSectionProps {
    firstName: string;
    streak: number;
    totalActivities: number;
    todayActivities: number;
}

const HeroSection = ({ firstName, streak, totalActivities, todayActivities }: HeroSectionProps) => {
    const [greeting, setGreeting] = useState("Hello");

    useEffect(() => {
        const hour = new Date().getHours();
        if (hour < 12) {
            setGreeting("Good morning");
        } else if (hour < 17) {
            setGreeting("Good afternoon");
        } else {
            setGreeting("Good evening");
        }
    }, []);

    // Dynamic tagline based on activity
    const getTagline = () => {
        if (streak >= 7) return "You're on fire!";
        if (todayActivities >= 3) return "Amazing progress today!";
        if (totalActivities >= 50) return "Learning champion";
        return "Your learning hub";
    };

    return (
        <section className={styles.hero}>
            {/* Badge */}
            <div className={styles.badge}>
                {streak > 0 ? <Flame size={14} /> : <Sparkles size={14} />}
                <span>{streak > 0 ? `${streak} Day Streak` : getTagline()}</span>
            </div>

            {/* Main Typography */}
            <h1 className={styles.title}>
                {greeting}, <span className={styles.muted}>{firstName}.</span> <br />
                <span className={styles.accent}>Ready to learn?</span>
            </h1>

            {/* Subtitle */}
            <p className={styles.subtitle}>
                Your personalized dashboard for tracking progress, accessing AI tools, and achieving your learning goals.
            </p>
        </section>
    );
};

export default HeroSection;
