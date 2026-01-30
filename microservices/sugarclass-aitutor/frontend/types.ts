
export interface DocumentImage {
  caption?: string;
  description?: string;
  base64_data: string;
  explanation?: string;
}

export enum Role {
  USER = 'user',
  MODEL = 'model',
  SYSTEM = 'system'
}

export interface Source {
  file_id: string;
  filename: string;
  chunk_id: number;
  score: number;
  text_preview: string;
  content_preview?: string;
}

export interface Message {
  id: string;
  role: Role;
  text: string;
  timestamp: Date;
  sources?: Source[];
  diagram?: string;
  documentImages?: DocumentImage[];
  ocrText?: string;
}

export interface ChatSession {
  id: string;
  messages: Message[];
}
