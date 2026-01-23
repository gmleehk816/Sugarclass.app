import { FileData, Source, DocumentImage } from '../types';

// API Base URL - uses relative URLs for nginx proxy
// Requests go through nginx at /api/ which proxies to tutor-service:8000
const API_BASE_URL = '/api';

// Tutor API endpoints
const TUTOR_API_BASE = `${API_BASE_URL}/tutor`;


export interface QueryResponse {
    answer: string;
    sources?: Source[];
    ocr_text?: string;
    document_images?: DocumentImage[];
    has_diagram?: boolean;
    diagram?: string;
}

export interface UploadResponse {
    file_id: string;
    filename: string;
    file_type: string;
    chunk_count: number;
    status: string;
    message: string;
}

export interface HealthResponse {
    status: string;
    version?: string;
    vector_store?: string;
    embedding_model?: string;
    document_count?: number;
}

export interface Subject {
    id: number;
    name: string;
    syllabus: string;
}

export interface SubjectsResponse {
    subjects: Subject[];
    count: number;
}

export interface StartSessionRequest {
    user_id: string;
    name?: string;
    grade_level?: string;
    curriculum?: string;
    subject?: string;
    topic?: string;
}

export interface StartSessionResponse {
    session_id: string;
    student_id: number;
    message: string;
    created_at: string;
}

export interface ChatRequest {
    session_id: string;
    message: string;
}

export interface ChatResponse {
    session_id: string;
    response: string;
    response_type: string;
    intent?: string;
    quiz_active: boolean;
    metadata: {
        turn_count?: number;
        current_topic?: string;
        detected_subject?: string;
        sources?: Source[];
    };
}

// Get system health status
export const getHealth = async (): Promise<HealthResponse> => {
    try {
        const response = await fetch(`${API_BASE_URL}/health`);
        if (!response.ok) {
            throw new Error('Backend is not healthy');
        }
        return response.json();
    } catch (error) {
        // Try tutor health endpoint
        const response = await fetch(`${TUTOR_API_BASE}/health`);
        if (!response.ok) {
            throw new Error('Backend is not healthy');
        }
        return response.json();
    }
};

// Get all available subjects
export const getSubjects = async (): Promise<SubjectsResponse> => {
    const response = await fetch(`${TUTOR_API_BASE}/subjects`);
    if (!response.ok) {
        throw new Error('Failed to fetch subjects');
    }
    return response.json();
};

// Start a new tutor session
export const startTutorSession = async (request: StartSessionRequest): Promise<StartSessionResponse> => {
    const response = await fetch(`${TUTOR_API_BASE}/session/start`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to start session');
    }

    return response.json();
};

// Send a chat message to the tutor
export const chatWithTutor = async (request: ChatRequest): Promise<ChatResponse> => {
    const response = await fetch(`${TUTOR_API_BASE}/chat`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(request),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to send message');
    }

    return response.json();
};

// Query documents with a question (RAG fallback)
export const queryDocuments = async (
    question: string,
    imageBase64?: string,
    topK: number = 5
): Promise<QueryResponse> => {
    const response = await fetch(`${API_BASE_URL}/query`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({
            question,
            image_base64: imageBase64,
            top_k: topK,
        }),
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to query documents');
    }

    return response.json();
};

// Stream query response (RAG fallback)
export const streamQuery = async (
    question: string,
    onChunk: (chunk: string) => void,
    onError: (error: string) => void,
    onComplete: () => void
): Promise<void> => {
    try {
        const response = await fetch(`${API_BASE_URL}/query/stream`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ question }),
        });

        if (!response.ok || !response.body) {
            throw new Error(`Streaming unavailable (status ${response.status})`);
        }

        const reader = response.body.getReader();
        const decoder = new TextDecoder('utf-8');
        let buffer = '';

        while (true) {
            const { value, done } = await reader.read();
            if (done) break;

            buffer += decoder.decode(value, { stream: true });
            let boundary = buffer.indexOf('\n\n');

            while (boundary !== -1) {
                const rawEvent = buffer.slice(0, boundary);
                buffer = buffer.slice(boundary + 2);
                const lines = rawEvent.split('\n');

                for (const line of lines) {
                    const trimmed = line.trim();
                    if (!trimmed.startsWith('data:')) continue;

                    const dataStr = trimmed.slice(5).trim();
                    if (!dataStr) continue;

                    const payload = JSON.parse(dataStr);

                    if (payload.type === 'chunk') {
                        onChunk(payload.text || '');
                    } else if (payload.type === 'done') {
                        onComplete();
                        return;
                    } else if (payload.type === 'error') {
                        onError(payload.message || 'Streaming error occurred.');
                        return;
                    }
                }

                boundary = buffer.indexOf('\n\n');
            }
        }
    } catch (error) {
        onError(error instanceof Error ? error.message : 'Failed to stream query');
    }
};

// Upload a file to the backend
export const uploadFile = async (file: File): Promise<UploadResponse> => {
    const formData = new FormData();
    formData.append('file', file);

    const response = await fetch(`${API_BASE_URL}/upload`, {
        method: 'POST',
        body: formData,
    });

    if (!response.ok) {
        const error = await response.json();
        throw new Error(error.detail || 'Failed to upload file');
    }

    return response.json();
};

// Clear all documents from the backend
export const clearAllDocuments = async (): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/documents`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error('Failed to clear documents');
    }
};

// Delete a specific document by file ID
export const deleteDocument = async (fileId: string): Promise<void> => {
    const response = await fetch(`${API_BASE_URL}/documents/${fileId}`, {
        method: 'DELETE',
    });

    if (!response.ok) {
        throw new Error('Failed to delete document');
    }
};

// Get system statistics
export const getStats = async () => {
    const response = await fetch(`${API_BASE_URL}/stats`);

    if (!response.ok) {
        throw new Error('Failed to get stats');
    }

    return response.json();
};

// End a tutor session
export const endTutorSession = async (sessionId: string): Promise<void> => {
    const response = await fetch(`${TUTOR_API_BASE}/session/end`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify({ session_id: sessionId }),
    });

    if (!response.ok) {
        throw new Error('Failed to end session');
    }
};
