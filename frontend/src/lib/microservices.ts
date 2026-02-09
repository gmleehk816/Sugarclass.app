const isProduction = typeof window !== 'undefined' && !window.location.hostname.includes('localhost');

export const SERVICE_URLS = {
    aimaterials: isProduction ? '/services/aimaterials' : 'http://localhost:8004',
    tutor: isProduction ? '/services/tutor' : 'http://localhost:8002',
    writer: isProduction ? '/services/writer' : 'http://localhost:8001',
    examiner: isProduction ? '/services/examiner' : 'http://localhost:8003',
};

export async function serviceFetch(service: keyof typeof SERVICE_URLS, endpoint: string, options: RequestInit = {}) {
    const baseUrl = SERVICE_URLS[service];

    // For file uploads, don't set Content-Type header manually
    const headers: Record<string, string> = {};
    if (!(options.body instanceof FormData)) {
        headers['Content-Type'] = 'application/json';
    }

    const response = await fetch(`${baseUrl}${endpoint}`, {
        ...options,
        headers: {
            ...headers,
            ...options.headers as any,
        },
    });

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'Service request failed' }));
        const errorMessage = typeof error.detail === 'string'
            ? error.detail
            : JSON.stringify(error.detail) || 'Service request failed';
        console.error(`Service error [${service}${endpoint}]:`, error);
        throw new Error(errorMessage);
    }

    return response.json();
}
