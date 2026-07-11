export const API_ENDPOINTS = {
  login: "/auth/login",
  demoUsers: "/auth/demo-users",
  documents: "/documents",
  document: (id: string) => `/documents/${encodeURIComponent(id)}`,
  search: "/search",
  chat: "/chat/ask",
} as const;
