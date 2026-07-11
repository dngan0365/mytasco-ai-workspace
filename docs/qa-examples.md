# 10 câu hỏi mẫu & 5 permission test case

Toàn bộ dữ liệu bên dưới lấy trực tiếp từ sheet `Public_Evaluation` trong dataset
(`ai_workspace_dataset_vietnamese_participants.xlsx`) và đã được **chạy xác nhận
qua hệ thống thật** (`GET /evaluation/run`), không phải số liệu tự dựng.

Chạy lại toàn bộ 50 câu bất kỳ lúc nào:

```bash
curl -s localhost:8000/evaluation/run | python3 -m json.tool
```

## 1. Mười câu hỏi mẫu (đa dạng vai trò, phòng ban, mức độ khó)

| ID | Câu hỏi | Người hỏi (vai trò · phòng ban) | Loại câu trả lời | Độ khó |
|---|---|---|---|---|
| P001 | Chính sách thử việc là gì? | Employee · Human Resources | Exact | Easy |
| P002 | Nhân viên được bao nhiêu ngày nghỉ phép năm? | Manager · Finance | Exact | Easy |
| P003 | Làm thế nào để nộp yêu cầu hoàn ứng chi phí? | Employee · Finance | Semantic | Easy |
| P004 | Quy trình phát hành sản phẩm gồm những giai đoạn nào? | Employee · Product | Summary | Medium |
| P005 | Làm thế nào để yêu cầu môi trường phát triển mới? | Employee · Engineering | Semantic | Easy |
| P006 | Chính sách lưu trữ hồ sơ quy định hợp đồng được lưu bao lâu? | Director · Legal & Compliance | Exact | Easy |
| P007 | Ưu tiên chiến lược của công ty năm 2026 là gì? | Director · Product | Permission (kỳ vọng **Deny**) | Medium |
| P008 | Ưu tiên chiến lược của công ty năm 2026 là gì? (cùng câu hỏi) | Executive · Executive Office | Summary (kỳ vọng **Allow**) | Medium |
| P009 | Khung lương Product Manager là bao nhiêu? | Employee · Engineering | Permission (kỳ vọng **Deny**) | Medium |
| P010 | Khung lương Product Manager là bao nhiêu? (cùng câu hỏi) | Employee · Human Resources | Exact (kỳ vọng **Allow**) | Medium |

Chú ý các cặp P007/P008 và P009/P010: **cùng một câu hỏi**, khác người hỏi →
khác kết quả — đây chính là bằng chứng rõ nhất cho việc AI trả lời khác nhau
tuỳ theo quyền, chứ không phải một câu trả lời cứng cho mọi người.

## 2. Năm permission test case (đã chạy xác nhận, bao phủ đủ 4 mức classification)

| # | Câu hỏi | Người dùng | Classification tài liệu | Kỳ vọng | Kết quả thực tế | Tài liệu truy xuất (AI Search) |
|---|---|---|---|---|---|---|
| 1 | Chính sách thử việc là gì? | Nguyễn Văn An — Employee, HR | Public | **Allow** | ✅ Allow | DOC002, **DOC001**, DOC011, DOC009, DOC035 |
| 2 | Khung lương Product Manager là bao nhiêu? | Phạm Quốc Dũng — Employee, Engineering | Confidential (thuộc HR) | **Deny** (khác phòng ban) | ✅ Deny | DOC020, DOC002, DOC004, DOC026, DOC025 *(DOC007 không xuất hiện)* |
| 3 | Khung lương Product Manager là bao nhiêu? | Nguyễn Văn An — Employee, HR | Confidential (thuộc HR) | **Allow** (cùng phòng ban) | ✅ Allow | **DOC007**, DOC020, DOC002, DOC004, DOC026 |
| 4 | Ưu tiên chiến lược công ty 2026 là gì? | Lê Minh Châu — Director, Product | Restricted | **Deny** (không phải Executive) | ✅ Deny | DOC016, DOC034, DOC004, DOC001, DOC032 *(DOC036 không xuất hiện)* |
| 5 | Ưu tiên chiến lược công ty 2026 là gì? | Vũ Thị Lan — Executive, Executive Office | Restricted | **Allow** (Executive) | ✅ Allow | **DOC036**, DOC038, DOC016, DOC037, DOC034 |

Test case #2 và #4 minh hoạ đúng nguyên tắc **không tiết lộ sự tồn tại của tài
liệu bị khoá**: `DOC007`/`DOC036` hoàn toàn không xuất hiện trong danh sách
tài liệu trả về, thay vì xuất hiện kèm thông báo "bạn không có quyền".

## 3. Độ chính xác đo được trên toàn bộ 50 câu

| Chỉ số | Giá trị |
|---|---|
| Permission accuracy | 98% (49/50) |
| Retrieval accuracy | 100% (50/50) |

## 4. Ghi chú minh bạch về chất lượng dữ liệu (đã kiểm chứng, không phải bug hệ thống)

- **Câu P035** (`DOC030`, hỏi về KPI vận hành): tài liệu được gắn
  `classification: Internal` — theo đúng ma trận phân quyền, Internal luôn
  **Allow cho mọi vai trò**. Nhãn kỳ vọng trong sheet `Public_Evaluation` lại
  ghi `Deny`. Hệ thống **tuân thủ đúng luật đã công bố** (Allow) thay vì khớp
  nhãn — đây là 1/50 điểm được xem là không nhất quán trong dataset, không
  phải lỗi logic RBAC.
- **Câu P007** (bảng trên): cột `user_role` trong sheet ghi "Employee" cho
  `U003`, nhưng bảng `Users` (nguồn dữ liệu gốc, luôn được hệ thống đọc trực
  tiếp) ghi `U003` là **Director**. Hệ thống dùng đúng vai trò thật từ `Users`
  — kết quả Deny vẫn đúng vì Director cũng không có quyền xem tài liệu
  Restricted, nhưng đáng lưu ý cho ai đối chiếu thủ công bằng mắt.
