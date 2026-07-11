const apiUrl = process.env.NEXT_PUBLIC_API_URL?.trim();

export const env = {
  apiUrl: (apiUrl || "http://localhost:8000").replace(/\/$/, ""),
};
