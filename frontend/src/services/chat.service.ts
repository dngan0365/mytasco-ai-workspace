import { API_ENDPOINTS } from "@/constants/api-endpoints"; import { http } from "./api-client";
export interface ChatSource { document_id: string; title: string; classification: string }
export interface ChatResponse { answer: string; sources: ChatSource[]; mode: string; intent: string }
export const chatService = { ask: (question: string) => http.post<ChatResponse, { question: string }>(API_ENDPOINTS.chat, { question }) };
