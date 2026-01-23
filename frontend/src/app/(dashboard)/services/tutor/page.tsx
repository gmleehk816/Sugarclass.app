"use client";

import ServiceFrame from "@/components/ServiceFrame";

export default function TutorPage() {
    return (
        <ServiceFrame
            name="AI Tutor"
            description="Institutional-grade conceptual synthesis and adaptive learning oracle. Validates neural progress in real-time."
            serviceUrl="http://localhost:3002" // Port 3002 is for AI Tutor
        />
    );
}
