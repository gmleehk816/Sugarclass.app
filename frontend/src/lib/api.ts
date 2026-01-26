const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000/api/v1";

export async function apiFetch(endpoint: string, options: RequestInit = {}) {
    const token = typeof window !== 'undefined' ? localStorage.getItem('token') : null;

    const headers = {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
        ...options.headers,
    };

    const response = await fetch(`${API_URL}${endpoint}`, {
        ...options,
        headers,
    });

    if (response.status === 401) {
        if (typeof window !== 'undefined') {
            localStorage.removeItem('token');
            window.location.href = '/login';
        }
    }

    if (!response.ok) {
        const error = await response.json().catch(() => ({ detail: 'An error occurred' }));
        throw new Error(error.detail || 'API request failed');
    }

    return response.json();
}

export const auth = {
    login: (data: any) => {
        const formData = new FormData();
        formData.append('username', data.email);
        formData.append('password', data.password);

        return fetch(`${API_URL}/auth/login`, {
            method: 'POST',
            body: formData,
        }).then(r => r.json());
    },
    register: (data: any) => apiFetch('/auth/register', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
    me: () => apiFetch('/auth/me'),
};

export const progress = {
    getSummary: () => apiFetch('/progress/summary'),
    getFullHistory: (limit: number = 50) => apiFetch(`/progress/history?limit=${limit}`),
    trackActivity: (data: any) => apiFetch('/progress/', {
        method: 'POST',
        body: JSON.stringify(data),
    }),
};
