import { z } from "zod";
export const documentSchema = z.object({ title: z.string().trim().min(3, "Tiêu đề cần ít nhất 3 ký tự.").max(160), department: z.string().min(1, "Vui lòng chọn phòng ban."), classification: z.string().min(1, "Vui lòng chọn mức bảo mật."), content_vi: z.string().trim().min(20, "Nội dung cần ít nhất 20 ký tự."), tags: z.string().optional() });
export type DocumentFormValues = z.infer<typeof documentSchema>;
