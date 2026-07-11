export function formatDate(value?: string) { if (!value) return "Chưa cập nhật"; const date = new Date(value); return Number.isNaN(date.getTime()) ? value : new Intl.DateTimeFormat("vi-VN", { day: "2-digit", month: "short", year: "numeric" }).format(date); }
export function formatNumber(value?: number | null) { return new Intl.NumberFormat("vi-VN").format(value ?? 0); }
