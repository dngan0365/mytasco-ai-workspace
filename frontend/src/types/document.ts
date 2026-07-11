export interface Document { document_id: string; title: string; department: string; classification: string; owner?: string | null; tags?: string | null; last_updated?: string; word_count?: number | null; content_vi?: string; allowed_access?: string | null }
export interface DocumentPayload { title: string; department: string; classification: string; content_vi: string; tags?: string }
export interface SearchResult extends Document { score: number }
