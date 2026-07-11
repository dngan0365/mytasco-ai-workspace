import { API_ENDPOINTS } from "@/constants/api-endpoints";
import type { LoginResponse, User } from "@/types/auth";
import { http } from "./api-client";
export const authService = { getDemoUsers: () => http.get<User[]>(API_ENDPOINTS.demoUsers), login: (userId: string) => http.post<LoginResponse, { user_id: string }>(API_ENDPOINTS.login, { user_id: userId }) };
