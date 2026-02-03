/**
 * API client for NewsCollect backend
 * Handles all communication with the FastAPI backend
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// Types
export interface Article {
    id: number;
    title: string;
    url?: string;
    source?: string;
    category?: string;
    age_group?: string;
    full_text?: string;
    description?: string;
    image_url?: string;
    published_at?: string;
    word_count?: number;
}

export interface PrewriteResponse {
    summary?: string;
    error?: string;
    success: boolean;
}

export interface SuggestionResponse {
    suggestion?: string;
    error?: string;
    success: boolean;
}

export interface ImprovementResponse {
    improved?: string;
    error?: string;
    success: boolean;
}

export interface StatsResponse {
    total_articles: number;
    by_category: Record<string, number>;
    by_age_group: Record<string, number>;
    by_source: Record<string, number>;
}

export interface CollectionStatus {
    running: boolean;
    last_started: string | null;
    last_completed: string | null;
    last_error: string | null;
    last_results: any[] | null;
}

export interface CollectionResponse {
    status: 'started' | 'already_running' | 'success';
    message: string;
    started_at?: string;
}

// Helper function for API requests
async function fetchAPI<T>(endpoint: string, options?: RequestInit): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;

    const token = typeof window !== 'undefined' ? localStorage.getItem('sugarclass_token') : null;

    const response = await fetch(url, {
        ...options,
        headers: {
            'Content-Type': 'application/json',
            ...(token ? { 'Authorization': `Bearer ${token}` } : {}),
            ...options?.headers,
        },
    });

    if (!response.ok) {
        // Try to extract error detail from response
        let errorMessage = `API Error: ${response.status} ${response.statusText}`;
        try {
            const errorData = await response.json();
            if (errorData.detail) {
                errorMessage = errorData.detail;
            } else if (errorData.error) {
                errorMessage = errorData.error;
            }
        } catch {
            // If response is not JSON, use status text
        }
        throw new Error(errorMessage);
    }

    return response.json();
}

/**
 * Get list of articles with optional filtering
 */
export async function getArticles(params?: {
    category?: string;
    age_group?: string;
    limit?: number;
    offset?: number;
}): Promise<Article[]> {
    const searchParams = new URLSearchParams();

    if (params?.category) searchParams.set('category', params.category);
    if (params?.age_group) searchParams.set('age_group', params.age_group);
    if (params?.limit) searchParams.set('limit', params.limit.toString());
    if (params?.offset) searchParams.set('offset', params.offset.toString());

    const query = searchParams.toString();
    const endpoint = `/articles${query ? `?${query}` : ''}`;

    return fetchAPI<Article[]>(endpoint);
}

/**
 * Get a single article by ID
 */
export async function getArticle(id: number | string): Promise<Article> {
    return fetchAPI<Article>(`/articles/${id}`);
}

/**
 * Generate a prewrite summary for an article
 */
export async function generatePrewrite(params: {
    title: string;
    text: string;
    year_level: string | number;
}): Promise<PrewriteResponse> {
    return fetchAPI<PrewriteResponse>('/ai/prewrite', {
        method: 'POST',
        body: JSON.stringify({
            title: params.title,
            text: params.text,
            year_level: params.year_level,
        }),
    });
}

/**
 * Generate AI writing suggestion based on user's text
 */
export async function generateSuggestion(params: {
    user_text: string;
    title: string;
    article_text: string;
    year_level: string | number;
    prewrite_summary?: string;
}): Promise<SuggestionResponse> {
    return fetchAPI<SuggestionResponse>('/ai/suggest', {
        method: 'POST',
        body: JSON.stringify({
            user_text: params.user_text,
            title: params.title,
            article_text: params.article_text,
            year_level: params.year_level,
            prewrite_summary: params.prewrite_summary,
        }),
    });
}

/**
 * Improve user's writing
 */
export async function improveText(params: {
    text: string;
    article_text: string;
    year_level: string | number;
    selected_text?: string;  // Optional selected text to focus on
}): Promise<ImprovementResponse> {
    return fetchAPI<ImprovementResponse>('/ai/improve', {
        method: 'POST',
        body: JSON.stringify({
            text: params.text,
            article_text: params.article_text,
            year_level: params.year_level,
            selected_text: params.selected_text,
        }),
    });
}

/**
 * Get database statistics
 */
export async function getStats(): Promise<StatsResponse> {
    return fetchAPI<StatsResponse>('/stats');
}

/**
 * Health check
 */
export async function healthCheck(): Promise<{ status: string; service: string; version: string }> {
    return fetchAPI('/health');
}

/**
 * Trigger news collection (returns immediately, runs in background)
 */
export async function triggerCollection(): Promise<CollectionResponse> {
    return fetchAPI<CollectionResponse>('/collect', {
        method: 'POST',
    });
}

/**
 * Get collection status
 */
export async function getCollectionStatus(): Promise<CollectionStatus> {
    return fetchAPI<CollectionStatus>('/collect/status');
}

/**
 * Save user's writing work
 */
export async function saveWriting(params: {
    article_id: number;
    title: string;
    content: string;
    content_html?: string;
    content_json?: string;
    word_count: number;
    year_level: string;
    milestone_message?: string;
    writing_id?: number;  // If provided, updates existing writing instead of creating new
}): Promise<{ success: boolean; writing_id?: number; error?: string }> {
    return fetchAPI('/ai/save-writing', {
        method: 'POST',
        body: JSON.stringify(params),
    });
}

export interface UserWriting {
    id: number;
    user_id: string;
    article_id: number;
    title: string;
    content: string;
    content_html?: string;
    content_json?: string;
    word_count: number;
    year_level?: string;
    milestone_message?: string;
    created_at: string;
    updated_at: string;
}

export interface MyWritingsResponse {
    writings: UserWriting[];
    success: boolean;
    error?: string;
}

/**
 * Get all user's saved writings
 */
export async function getMyWritings(): Promise<MyWritingsResponse> {
    return fetchAPI<MyWritingsResponse>('/ai/my-writings');
}
