'use client';

import { useEffect, Suspense } from 'react';
import { useSearchParams } from 'next/navigation';

function TokenCapture() {
    const searchParams = useSearchParams();

    useEffect(() => {
        const token = searchParams.get('token');
        if (token) {
            localStorage.setItem('sugarclass_token', token);
            // Clean up the URL
            const url = new URL(window.location.href);
            url.searchParams.delete('token');
            window.history.replaceState({}, '', url.toString());
        }
    }, [searchParams]);

    return null;
}

export default function SessionHandler() {
    return (
        <Suspense fallback={null}>
            <TokenCapture />
        </Suspense>
    );
}
