import axios, { type AxiosRequestConfig } from "axios";
import { env } from "@/config/env";
export const apiClient = axios.create({ baseURL: env.apiUrl, timeout: 30000, headers: { "Content-Type": "application/json", Accept: "application/json" } });
apiClient.interceptors.request.use((config) => { if (typeof window !== "undefined") { const token = localStorage.getItem("mytasco_access_token"); if (token) config.headers.Authorization = `Bearer ${token}`; } return config; });
export const http = {
  get: async <T>(url: string, config?: AxiosRequestConfig) => (await apiClient.get<T>(url, config)).data,
  post: async <T, B = unknown>(url: string, body?: B) => (await apiClient.post<T>(url, body)).data,
  put: async <T, B = unknown>(url: string, body?: B) => (await apiClient.put<T>(url, body)).data,
  patch: async <T, B = unknown>(url: string, body?: B) => (await apiClient.patch<T>(url, body)).data,
  delete: async <T>(url: string) => (await apiClient.delete<T>(url)).data,
};
