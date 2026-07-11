# Kiến trúc hệ thống — My Tasco AI Workspace

## 1. Tổng quan các service trong repo

```
mytasco-ai-workspace/
├── services/
│   ├── ingestion/        # Build chỉ mục tìm kiếm từ dataset (thay cho pipeline OCR/chunk/embed thật)
│   ├── orchestrator/      # FastAPI: RBAC, AI Search, AI Chat (LangGraph agent), tool-calling
│   └── mytasco-adapter/   # SDK Python dùng chung để gọi COP API (sys/hrm/aiwsp/noti)
├── infra/
│   ├── terraform/         # Hạ tầng AWS tối thiểu (S3, ECS, RDS, IAM) — skeleton để mở rộng
│   ├── mock-server/       # Mock COP API (Node.js) dùng khi chưa có gateway My Tasco thật
│   └── docker-compose.yml # Chạy Qdrant + Postgres + mock-server + orchestrator cùng lúc
├── docs/                  # Tài liệu này + access-control.md + qa-examples.md
├── frontend/              # Demo UI (Streamlit) gọi thẳng vào orchestrator
└── .github/workflows/     # CI, build & push image, deploy dev, terraform plan
```

## 2. Luồng dữ liệu — Ingestion

```
xlsx dataset (content_vi đã trích sẵn)
        │
        ▼
services/ingestion/build_index.py
  - gắn metadata phân quyền (classification, department, owner) cho từng doc
  - build TF-IDF index (sklearn, qua LangChain TFIDFRetriever)
        │
        ▼
output/knowledge_index.pkl  (artifact dùng chung)
        │
        ▼
services/orchestrator nạp artifact lúc khởi động (hoặc tự build từ xlsx nếu
chưa có artifact — xem app/data/loader.py)
```

Trong hệ thống thật (tài liệu PDF/DOCX/PPTX/ảnh thay vì xlsx có sẵn text),
bước này sẽ có thêm: OCR (Textract/Tesseract) → parsing (unstructured.io) →
chunking → gọi embedding model → ghi vào Qdrant thay vì TF-IDF in-memory.
Interface `BaseRetriever` của LangChain giúp việc thay thế này không ảnh
hưởng tới `agent/tools.py` hay `services/retrieval.py` phía trên.

## 3. Luồng truy vấn — AI Search & AI Chat

```
Client
  │  Bearer JWT (chứa role, department)
  ▼
FastAPI orchestrator (services/orchestrator)
  │
  ├── POST /search          → retrieval.py: TF-IDF search + loc ACL (can_access) → tra ve danh sach
  │
  └── POST /chat/ask
        │
        ├── Chua co OPENAI_API_KEY?
        │     → extractive fallback (retrieval.py, khong goi LLM/agent)
        │
        └── Co API key
              → LangGraph ReAct agent (app/agent/graph.py)
                    │
                    ├── Tool: search_knowledge_base   (RAG, loc ACL ben trong tool)
                    ├── Tool: search_staff_directory  ─┐
                    ├── Tool: list_hr_requests         │  goi qua mytasco-adapter
                    ├── Tool: get_staff_attendance     │  → mock-server (hoac COP gateway that)
                    ├── Tool: get_payslip (OTP-gated) ─┘
                    └── Tool: search_company_news
                    │
                    ▼
              OpenAI model (ChatOpenAI) tu quyet dinh goi tool nao, tong hop cau
              tra loi cuoi cung kem trich dan document_id
```

Điểm mấu chốt: **agent không tự viết router thủ công** — LLM tự quyết định
gọi tool nào dựa trên mô tả (docstring) của từng tool trong system prompt.
RBAC vẫn nằm ở tầng tool (`search_knowledge_base`), không phải ở system
prompt, nên không thể bị "prompt injection" qua mặt.

## 4. Sơ đồ agent (LangGraph ReAct)

```
                 ┌─────────────────────────┐
   Câu hỏi  ───▶ │   OpenAI model (ChatOpenAI) │
                 │   + system prompt        │
                 └────────────┬─────────────┘
                              │ chọn tool (0..n vòng lặp)
                              ▼
        ┌───────────────────────────────────────────┐
        │  search_knowledge_base │ search_staff_dir  │
        │  list_hr_requests      │ get_staff_attend. │
        │  get_payslip (OTP)     │ search_company_ne │
        └───────────────────────────────────────────┘
                              │ tool output (đã lọc ACL)
                              ▼
                 ┌─────────────────────────┐
                 │   OpenAI model tổng hợp câu    │
                 │   trả lời cuối + trích   │
                 │   dẫn document_id        │
                 └─────────────────────────┘
```

## 5. Stack công nghệ

| Thành phần | Lựa chọn hiện tại | Lựa chọn khi mở rộng production |
|---|---|---|
| Backend framework | FastAPI | (giữ nguyên) |
| Agent orchestration | LangGraph (`create_react_agent`) | (giữ nguyên, nâng cấp `langchain.agents` khi ổn định) |
| LLM | OpenAI model qua `langchain-openai` | (giữ nguyên, có thể thêm model mini/nano cho tác vụ rẻ) |
| Retriever | LangChain `TFIDFRetriever` (offline, không cần tải model) | Qdrant + embedding đa ngôn ngữ (bge-m3/Titan Embeddings) |
| Document store | xlsx dataset (đã có content_vi) | S3/MinIO + OCR (Textract/Tesseract) |
| Adapter nghiệp vụ | `mytasco-adapter` gọi mock COP server | Đổi `base_url` sang gateway COP thật |
| Metadata/permission | In-memory (từ xlsx) | Postgres (đã có trong `infra/docker-compose.yml`) |
| Hạ tầng | Docker Compose (local/demo) | AWS: ECS Fargate, RDS, S3, IAM (skeleton trong `infra/terraform`) |
| CI/CD | — | GitHub Actions: `ci.yml`, `build-push.yml`, `deploy-dev.yml`, `infra-plan.yml` |

## 6. Vì sao chọn LangGraph thay vì tự viết router state machine

- `create_react_agent` xử lý sẵn vòng lặp "gọi tool → nhận kết quả → gọi tool
  tiếp hoặc trả lời cuối" — không cần tự cài đặt state machine.
- Thêm tool mới (ví dụ thêm nghiệp vụ COP khác) chỉ cần viết thêm 1 hàm có
  decorator `@tool` trong `agent/tools.py`, không cần sửa logic routing.
- Vì tool được build lại theo từng `user` (closure), RBAC luôn đi kèm đúng
  ngữ cảnh của request, không bị rò rỉ giữa các request đồng thời.

