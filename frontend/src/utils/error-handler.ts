import axios from "axios";
import type { ApiErrorResponse } from "@/types/api";
export function getErrorMessage(error: unknown): string { if (axios.isAxiosError<ApiErrorResponse>(error)) { if (!error.response) return "Không thể kết nối máy chủ. Vui lòng kiểm tra backend."; return error.response.data?.detail || error.response.data?.message || `Yêu cầu thất bại (${error.response.status}).`; } return error instanceof Error ? error.message : "Đã xảy ra lỗi không xác định."; }
