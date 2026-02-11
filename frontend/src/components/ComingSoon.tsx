"use client";

import React from 'react';
import { Construction, Sparkles, ArrowLeft } from "lucide-react";
import Link from 'next/link';

interface ComingSoonProps {
    title: string;
    description: string;
}

const ComingSoon: React.FC<ComingSoonProps> = ({ title, description }) => {
    return (
        <div style={{
            height: '60vh',
            display: 'flex',
            flexDirection: 'column',
            alignItems: 'center',
            justifyContent: 'center',
            textAlign: 'center',
            gap: '24px'
        }}>
            <div style={{
                background: '#f8fafc',
                width: '120px',
                height: '120px',
                borderRadius: '50%',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
            }}>
                <Construction size={48} color="#94a3b8" />
            </div>

            <div>
                <h2 style={{ fontSize: '1.8rem', fontWeight: 800, color: '#1e293b', marginBottom: '12px' }}>{title}</h2>
                <p style={{ fontSize: '1rem', color: '#64748b', maxWidth: '400px', margin: '0 auto' }}>
                    {description}
                </p>
            </div>

            <div style={{ display: 'flex', gap: '16px' }}>
                <Link href="/admin" style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '12px 20px',
                    borderRadius: '12px',
                    border: '1px solid #e2e8f0',
                    background: 'white',
                    fontWeight: 600,
                    fontSize: '0.9rem',
                    color: '#475569'
                }}>
                    <ArrowLeft size={18} /> Back to Admin Panel
                </Link>
                <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px',
                    padding: '12px 20px',
                    borderRadius: '12px',
                    background: '#1e293b',
                    color: 'white',
                    fontWeight: 600,
                    fontSize: '0.9rem',
                    opacity: 0.8,
                    cursor: 'default'
                }}>
                    <Sparkles size={18} /> Coming Soon
                </div>
            </div>
        </div>
    );
};

export default ComingSoon;
