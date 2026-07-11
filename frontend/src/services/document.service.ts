import { API_ENDPOINTS } from "@/constants/api-endpoints";
import type { Document, DocumentPayload, SearchResult } from "@/types/document";
import { http } from "./api-client";
export const documentService = {
  getDocuments: () => http.get<Document[]>(API_ENDPOINTS.documents), getDocumentById: (id: string) => http.get<Document>(API_ENDPOINTS.document(id)),
  createDocument: (payload: DocumentPayload) => http.post<Document, DocumentPayload>(API_ENDPOINTS.documents, payload), updateDocument: (id: string, payload: DocumentPayload) => http.put<Document, DocumentPayload>(API_ENDPOINTS.document(id), payload), deleteDocument: (id: string) => http.delete<void>(API_ENDPOINTS.document(id)),
  search: (query: string, top_k = 8) => http.post<SearchResult[], { query: string; top_k: number }>(API_ENDPOINTS.search, { query, top_k }),
};
