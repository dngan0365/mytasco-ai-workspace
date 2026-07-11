# My Tasco AI Workspace

Enterprise Knowledge & Secure AI Search cho hệ sinh thái nội bộ My Tasco.

My Tasco AI Workspace là một nền tảng demo AI nội bộ gồm FastAPI Orchestrator, LangGraph Agent, OpenAPI-style Tool Gateway, RBAC/ACL, ingestion pipeline và Streamlit UI. Hệ thống cho phép người dùng tìm kiếm tài liệu, hỏi đáp bằng RAG, gọi các nghiệp vụ nội bộ như nhân sự/chấm công/đơn từ/lương/tin tức, đồng thời đảm bảo AI chỉ nhìn thấy dữ liệu mà người dùng được phép truy cập.

## Overview

Project này mô phỏng một AI Workspace doanh nghiệp:

- Người dùng đăng nhập bằng user demo trong dataset.
- Backend phát JWT chứa `role` và `department`.
- Search/chat request đi qua FastAPI Orchestrator.
- Retrieval luôn lọc RBAC/ACL trước khi trả kết quả hoặc đưa context vào LLM.
- Intent Router phân luồng câu hỏi sang RAG, tool nghiệp vụ hoặc human approval.
- LangGraph ReAct agent có thể gọi knowledge base và enterprise tools.
- Nếu chưa có `OPENAI_API_KEY`, hệ thống tự dùng extractive fallback để vẫn chạy local/CI.

Luồng tổng quát:

```text
User -> Streamlit / Swagger / API Client
     -> FastAPI Orchestrator
     -> JWT Auth
     -> Intent Router
     -> RAG Search | Tool Gateway | Human Approval
     -> Guardrails
     -> Response with answer, sources, mode, intent
```

## Project Objectives

- Xây dựng AI Search an toàn cho tài liệu nội bộ.
- Xây dựng AI Chat có citation, dựa trên tài liệu người dùng được phép xem.
- Chứng minh cơ chế permission-aware retrieval: lọc quyền ở backend/tool layer, không dựa vào prompt.
- Kết nối agent với nghiệp vụ My Tasco qua adapter và OpenAPI-style gateway.
- Cung cấp demo end-to-end chạy được bằng Python local, Docker Compose hoặc mock server.
- Chuẩn bị đường nâng cấp production: OCR, chunking, embeddings, Qdrant, Postgres, S3, ECS, CI/CD.

## Features

### AI Search

- Endpoint: `POST /search`.
- Tìm kiếm ngôn ngữ tự nhiên bằng TF-IDF cosine similarity.
- Over-fetch `top_k * 3`, sau đó lọc ACL để tránh lộ tài liệu không đủ quyền.
- Trả metadata và score, không trả toàn bộ `content_vi` trong danh sách search.

### AI Chat

- Endpoint: `POST /chat/ask`.
- Response gồm `answer`, `sources`, `mode`, `intent`.
- Có LangGraph agent khi cấu hình OpenAI API key thật.
- Có fallback extractive khi chưa có key, phù hợp demo offline và test.
- Có human approval response cho nhóm câu hỏi cần phê duyệt.

### Intent Router

Intent router nằm tại `services/orchestrator/app/agent/router.py`.

| Intent | Dấu hiệu | Handler |
|---|---|---|
| `rag` | chính sách, quy chế, quy trình, tài liệu, policy, document | Knowledge base search |
| `tool` | nhân viên, chấm công, đơn từ, lương, tin tức, thông báo | OpenAPI Tool Gateway |
| `human_approval` | duyệt, phê duyệt, tạo đơn, cấp quyền | Human approval node/response |

### OpenAPI Tool Gateway

Gateway nằm tại `services/orchestrator/app/agent/openapi_gateway.py` và expose manifest qua:

```text
GET /tools/openapi.json
```

Operations hiện có:

- `search_staff_directory`
- `list_hr_requests`
- `get_staff_attendance`
- `get_payslip`
- `search_company_news`
- `search_notifications`

Gateway gọi `services/mytasco-adapter`. Adapter có thể trỏ tới mock server local hoặc COP gateway thật bằng `MYTASCO_MOCK_BASE_URL`/base URL tương ứng.

### RBAC/ACL

Logic chính nằm tại `services/orchestrator/app/core/rbac.py`.

| Classification | Employee / Manager / Director | Executive |
|---|---|---|
| Public | Allow | Allow |
| Internal | Allow | Allow |
| Confidential | Allow nếu cùng department | Allow |
| Restricted | Deny | Allow |

Nguyên tắc: tài liệu bị chặn không được trả về client và cũng không được đưa vào context của LLM.

### Demo Frontend

Frontend Streamlit tại `frontend/app.py` có:

- Login bằng user mẫu.
- Tab AI Chat.
- Tab AI Search.
- Tab thư viện tài liệu đã lọc quyền.

## Architecture

```text
services/orchestrator
  FastAPI app
  ├─ auth router: login demo, JWT
  ├─ documents router: list/detail documents with ACL
  ├─ search router: TF-IDF retrieval with ACL
  ├─ chat router: intent + fallback/LangGraph agent
  ├─ tools router: OpenAPI manifest
  ├─ core/security.py: JWT encode/decode
  ├─ core/rbac.py: permission matrix
  ├─ data/loader.py: Excel dataset -> Store -> TF-IDF index
  └─ agent/: router, graph, tools, gateway, knowledge base

services/ingestion
  build_index.py -> output/knowledge_index.pkl

services/mytasco-adapter
  async httpx client for COP/mock API

infra/mock-server
  Node.js mock My Tasco API

frontend
  Streamlit demo UI
```

Runtime request flow:

```text
Client
  -> FastAPI
  -> get_current_user() from Bearer JWT
  -> route_intent(question)
  -> RAG: retrieve(user, query) -> can_access(user, document)
  -> TOOL: LangGraph tool -> OpenAPIToolGateway -> MyTascoClient
  -> Guardrail output
  -> JSON response
```

## Technology Stack

| Layer | Technology |
|---|---|
| Backend API | FastAPI, Uvicorn |
| Agent orchestration | LangGraph, LangChain |
| LLM provider | OpenAI model via `langchain-openai` |
| Retrieval demo | scikit-learn TF-IDF, cosine similarity |
| Dataset | Excel, pandas, openpyxl |
| Auth | JWT, PyJWT, FastAPI HTTPBearer |
| Frontend | Streamlit, httpx |
| Enterprise adapter | httpx async client |
| Mock API | Node.js |
| Local infra | Docker Compose, Qdrant, Postgres |
| Cloud skeleton | Terraform, AWS ECS/RDS/S3/IAM/Secrets Manager |
| Testing | pytest, pytest-asyncio |
| CI/CD | GitHub Actions |

## Project Structure

```text
mytasco-ai-workspace/
├── README.md
├── START_HERE.md
├── QUICK_REFERENCE.md
├── SETUP_AND_DEPLOYMENT.md
├── IMPLEMENTATION_STATUS.md
├── ARCHITECTURE_IMPLEMENTATION.md
├── ARCHITECTURE_UPDATE_SUMMARY.md
├── docs/
│   ├── architecture.md
│   ├── access-control.md
│   └── qa-examples.md
├── frontend/
│   ├── app.py
│   └── requirements.txt
├── services/
│   ├── ingestion/
│   │   ├── build_index.py
│   │   └── requirements.txt
│   ├── mytasco-adapter/
│   │   ├── pyproject.toml
│   │   └── mytasco_adapter/client.py
│   └── orchestrator/
│       ├── Dockerfile
│       ├── requirements.txt
│       ├── demo_architecture.py
│       ├── test_structure.py
│       ├── app/
│       │   ├── main.py
│       │   ├── agent/
│       │   ├── core/
│       │   ├── data/
│       │   ├── routers/
│       │   └── services/
│       └── tests/
├── infra/
│   ├── docker-compose.yml
│   ├── mock-server/
│   └── terraform/
└── .github/workflows/
    ├── ci.yml
    ├── build-push.yml
    ├── deploy-dev.yml
    └── infra-plan.yml
```

## Data Pipeline

### Current Demo Pipeline

Dataset hiện tại là file Excel có sẵn nội dung tiếng Việt trong `content_vi`.

```text
Excel dataset
  -> pandas reads sheets
  -> merge Documents + Document_Metadata
  -> normalize department aliases
  -> build users, roles, permissions, evaluation records
  -> build TF-IDF vectorizer and document matrix
  -> cache Store in memory
```

Khi app khởi động, `app.main` gọi `get_store()` trong lifespan. Loader sẽ:

1. Kiểm tra `INDEX_ARTIFACT_PATH`.
2. Nếu artifact tồn tại, nạp `knowledge_index.pkl`.
3. Nếu artifact không tồn tại, đọc dataset Excel.
4. Build TF-IDF index trong memory.
5. Cache Store bằng `lru_cache`.

### Build Index Artifact

```bash
cd services/ingestion
pip install -r requirements.txt
python build_index.py
```

Output mặc định:

```text
services/ingestion/output/knowledge_index.pkl
```

### Production Pipeline Direction

Khi thay dataset demo bằng tài liệu thật:

```text
PDF/DOCX/PPTX/Image
  -> S3/document store
  -> OCR with Textract/Tesseract
  -> parsing with unstructured.io or native parsers
  -> chunking
  -> embeddings
  -> Qdrant/vector database
  -> metadata and ACL in Postgres
  -> permission-aware retrieval
```

## Dataset

Dataset chính:

```text
services/orchestrator/app/data/ai_workspace_dataset_vietnamese_participants.xlsx
```

Các sheet được dùng:

| Sheet | Mục đích |
|---|---|
| `Documents` | Nội dung, title, department, classification, `content_vi` |
| `Document_Metadata` | Owner, tags, allowed access, last updated, word count |
| `Users` | User demo, role, department |
| `Departments` | Department ID, tên Anh/Việt, alias |
| `Roles` | Vai trò |
| `Permissions` | Ma trận phân quyền |
| `Public_Evaluation` | Câu hỏi đánh giá |

Classification chính: `Public`, `Internal`, `Confidential`, `Restricted`.

Role demo chính: `Employee`, `Manager`, `Director`, `Executive`.

## Installation

### Prerequisites

- Python 3.10+.
- pip.
- Node.js 20 nếu chạy mock server thủ công.
- Docker Compose nếu chạy full stack container.
- OpenAI API key nếu muốn bật LangGraph agent thật.

### Create Virtual Environment

Windows PowerShell:

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip setuptools wheel
```

macOS/Linux:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip setuptools wheel
```

### Install Backend

```bash
cd services/orchestrator
pip install -r requirements.txt
```

`requirements.txt` đã khai báo:

```text
-e ../mytasco-adapter
```

Nếu cần cài adapter riêng:

```bash
cd services/mytasco-adapter
pip install -e .
```

### Install Frontend

```bash
cd frontend
pip install -r requirements.txt
```

### Install Mock Server

```bash
cd infra/mock-server
npm install
```

## Configuration

Orchestrator đọc config từ environment variables hoặc file `.env` trong `services/orchestrator`.

Ví dụ `.env`:

```env
APP_NAME="My Tasco AI Workspace"
JWT_SECRET="please-change-me-in-production"
JWT_ALGORITHM="HS256"
JWT_EXPIRE_MINUTES=480
DATASET_PATH="app/data/ai_workspace_dataset_vietnamese_participants.xlsx"
INDEX_ARTIFACT_PATH="../ingestion/output/knowledge_index.pkl"
OPENAI_API_KEY=""
OPENAI_MODEL="gpt-4.1-mini"
TOP_K_RETRIEVAL=4
MYTASCO_MOCK_BASE_URL="http://localhost:8788"
```

| Variable | Default | Ý nghĩa |
|---|---|---|
| `JWT_SECRET` | `please-change-me-in-production` | Secret ký JWT demo |
| `JWT_ALGORITHM` | `HS256` | Thuật toán JWT |
| `JWT_EXPIRE_MINUTES` | `480` | Thời hạn token |
| `DATASET_PATH` | `app/data/...xlsx` | Đường dẫn dataset |
| `INDEX_ARTIFACT_PATH` | `../ingestion/output/knowledge_index.pkl` | Artifact index |
| `OPENAI_API_KEY` | empty | Bật agent thật nếu là key hợp lệ |
| `OPENAI_MODEL` | `gpt-4.1-mini` | OpenAI model |
| `TOP_K_RETRIEVAL` | `4` | Số kết quả retrieval mặc định |
| `MYTASCO_MOCK_BASE_URL` | `http://localhost:8788` | Base URL mock/COP API |

Không commit `.env` chứa secret thật.

## Running the Project

### Backend Only

```bash
cd services/orchestrator
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Health check:

```bash
curl http://localhost:8000/health
```

Swagger UI:

```text
http://localhost:8000/docs
```

### Frontend

Chạy backend trước, sau đó:

```bash
cd frontend
streamlit run app.py
```

### Mock My Tasco API

```bash
cd infra/mock-server
npm install
node mock_mytasco_server.js
```

Mock server chạy tại `http://localhost:8788`.

### Docker Compose

```bash
cd infra
docker compose up --build
```

Compose chạy:

- `qdrant`: `localhost:6333`.
- `postgres`: `localhost:5432`.
- `mytasco-mock`: `localhost:8788`.
- `orchestrator`: `localhost:8000`.

Trong bản demo hiện tại, Qdrant và Postgres là skeleton cho production, chưa bắt buộc cho TF-IDF retrieval.

### Architecture Demo

```bash
cd services/orchestrator
python demo_architecture.py
```

## Workflow

### User Flow

1. Gọi `GET /auth/demo-users` để xem user mẫu.
2. Gọi `POST /auth/login` với `user_id`.
3. Nhận JWT access token.
4. Gửi token trong `Authorization: Bearer <token>`.
5. Gọi `/search`, `/chat/ask`, `/documents`.
6. Backend xác thực token, lấy role/department.
7. Retrieval/tool được gọi trong đúng ngữ cảnh user.
8. RBAC lọc dữ liệu trước khi trả response.

### Login Example

```bash
curl http://localhost:8000/auth/demo-users
```

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"user_id\":\"U001\"}"
```

### Search Example

```bash
curl -X POST http://localhost:8000/search \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"query\":\"quy chế nghỉ phép\",\"top_k\":5}"
```

### Chat Example

```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d "{\"question\":\"Quy chế nghỉ phép của công ty là gì?\"}"
```

### Tool Manifest Example

```bash
curl http://localhost:8000/tools/openapi.json
```

## Data Model

### Store

Runtime data model chính nằm trong `services/orchestrator/app/data/loader.py`:

```python
@dataclass
class Store:
    documents: dict[str, dict]
    users: dict[str, dict]
    departments: list[dict]
    department_alias: dict[str, str]
    roles: list[dict]
    permissions: list[dict]
    evaluation: list[dict]
    vectorizer: TfidfVectorizer
    doc_ids: list[str]
    doc_matrix: Any
```

### Document

Document được ghép từ `Documents` và `Document_Metadata`:

- `document_id`
- `title`
- `department`
- `classification`
- `content_vi`
- `owner`
- `allowed_access`
- `tags`
- `last_updated`
- `word_count`

### User

User demo có các trường chính:

- `user_id`
- `full_name`
- `role`
- `department`

JWT chứa:

- `sub`
- `role`
- `department`
- `full_name`
- `iat`
- `exp`

### Chat Response

```json
{
  "answer": "string",
  "sources": [
    {
      "document_id": "DOC001",
      "title": "Document title",
      "classification": "Internal"
    }
  ],
  "mode": "extractive_fallback | langgraph-agent | human_approval | no_context",
  "intent": "rag | tool | human_approval"
}
```

## Testing

Chạy toàn bộ test:

```bash
cd services/orchestrator
pytest -v
```

Chạy từng nhóm:

```bash
pytest tests/test_rbac.py -v
pytest tests/test_api.py -v
pytest tests/test_agent.py -v
```

Structure/demo checks:

```bash
python test_structure.py
python demo_architecture.py
```

Evaluation endpoint khi backend đang chạy:

```bash
curl -s http://localhost:8000/evaluation/run | python -m json.tool
```

## Monitoring

Hiện project chưa tích hợp Prometheus/Grafana/OpenTelemetry đầy đủ. Các metric nên bổ sung khi production:

- Request latency theo route.
- Error rate theo route.
- Số request chat/search/documents.
- Phân bố intent: `rag`, `tool`, `human_approval`.
- Tỷ lệ `extractive_fallback` do thiếu LLM key.
- Số lần RBAC deny.
- Số lần guardrail block.
- Tool gateway latency/error.
- Retrieval latency và result count.

Metric gợi ý:

| Metric | Ý nghĩa |
|---|---|
| `http_request_duration_seconds` | API latency |
| `chat_requests_total` | Tổng chat request |
| `chat_intent_total` | Phân bố intent |
| `rbac_denied_total` | Lượt bị chặn bởi ACL |
| `tool_gateway_errors_total` | Lỗi gọi API nghiệp vụ |
| `guardrail_blocks_total` | Output bị guardrail chặn |

## Logging

Hiện tại chủ yếu dùng log mặc định của Uvicorn/FastAPI:

```bash
uvicorn app.main:app --reload --log-level info
```

Nên bổ sung structured logging cho production:

- Auth success/failure.
- Search metadata: user_id, role, department, top_k, result_count.
- Chat metadata: intent, mode, source_count, latency.
- Tool call: operation_id, success/failure, latency.
- RBAC deny: role, document classification, department mismatch.
- Guardrail block: category, request id.

Không nên log JWT đầy đủ, API key, OTP, payslip, lương, hoặc toàn bộ nội dung tài liệu nhạy cảm.

## Performance Optimization

Tối ưu hiện có:

- Store và TF-IDF index được cache bằng `lru_cache`.
- App warm-up dataset trong FastAPI lifespan.
- Retrieval over-fetch để bù kết quả bị ACL loại bỏ.
- Fallback mode không gọi LLM, nhanh và ổn định cho CI/demo.
- Tool adapter dùng async `httpx`.

Hướng tối ưu tiếp theo:

- Build sẵn `knowledge_index.pkl` để giảm startup time.
- Dùng Qdrant + embeddings cho tập tài liệu lớn.
- Cache query phổ biến theo role/department.
- Chuyển metadata/permission sang Postgres.
- Thêm timeout/retry/circuit breaker cho tool gateway.
- Streaming chat response.
- Batch embedding trong ingestion pipeline.

## Security

Controls hiện có:

- Endpoint nhạy cảm yêu cầu Bearer JWT.
- JWT chứa role/department để thực thi phân quyền.
- RBAC/ACL áp dụng trước LLM.
- `Restricted` chỉ cho `Executive`.
- `Confidential` chỉ cho cùng department hoặc `Executive`.
- Payslip yêu cầu OTP trong gateway response.
- Guardrail chặn một số pattern nhạy cảm trong output.

Việc cần làm trước production:

- Thay login demo bằng SSO/COP Auth thật.
- Đổi `JWT_SECRET` mặc định.
- Giới hạn CORS, không để `allow_origins=["*"]` trong production.
- Quản lý secret bằng AWS Secrets Manager hoặc secret store tương đương.
- Bật audit log cho Confidential/Restricted.
- Chuẩn hóa mapping user dataset với `staffId` COP thật.
- Mã hóa dữ liệu at rest cho S3/RDS/vector store.
- Thiết lập policy cho prompt/log retention.

## CI/CD

Repo có workflow trong `.github/workflows`:

| Workflow | Mục đích |
|---|---|
| `ci.yml` | Lint/test/build checks |
| `build-push.yml` | Build và push Docker image |
| `deploy-dev.yml` | Deploy môi trường dev |
| `infra-plan.yml` | Terraform plan cho thay đổi hạ tầng |

Pipeline khuyến nghị:

```text
Pull Request
  -> ci.yml
  -> pytest
  -> review
  -> merge main
  -> build-push.yml
  -> deploy-dev.yml
  -> smoke test
```

Với Terraform:

```text
Change infra/terraform
  -> infra-plan.yml
  -> review plan
  -> manual approval
  -> terraform apply
```

Secrets thường cần: AWS credentials/OIDC role, registry token, `OPENAI_API_KEY`, `JWT_SECRET`, database password.

## Future Improvements

- Thay TF-IDF bằng Qdrant + multilingual embeddings.
- Bổ sung OCR/parsing cho PDF, DOCX, PPTX, ảnh.
- Lưu metadata, ACL và audit trail trong Postgres.
- Xây admin UI upload tài liệu và gắn classification.
- Thêm streaming chat.
- Thêm conversation memory có kiểm soát quyền.
- Mở rộng tool gateway cho nhiều nghiệp vụ COP hơn.
- Làm human approval queue thật.
- Thêm OpenTelemetry, Prometheus, Grafana.
- Thêm rate limit theo user/role.
- Thêm evaluation cho faithfulness, citation accuracy, permission accuracy.
- Thêm test chống prompt injection và data exfiltration.

## Troubleshooting

### `ModuleNotFoundError: No module named 'mytasco_adapter'`

```bash
cd services/mytasco-adapter
pip install -e .
```

Hoặc:

```bash
cd services/orchestrator
pip install -r requirements.txt
```

### `Thiếu Bearer token`

Gọi login trước rồi gửi header:

```text
Authorization: Bearer <token>
```

### `Token không hợp lệ hoặc đã hết hạn`

Đăng nhập lại bằng `/auth/login`. Token demo hết hạn theo `JWT_EXPIRE_MINUTES`.

### Không có `OPENAI_API_KEY`

Không bắt buộc. Hệ thống sẽ chạy `extractive_fallback`. Nếu muốn bật agent thật, đặt:

```env
OPENAI_API_KEY="sk-..."
```

### Không đọc được dataset

Chạy backend từ đúng thư mục:

```bash
cd services/orchestrator
uvicorn app.main:app --reload --port 8000
```

Hoặc đặt `DATASET_PATH` là absolute path.

### Mock server không kết nối được

```bash
cd infra/mock-server
npm install
node mock_mytasco_server.js
```

Kiểm tra `MYTASCO_MOCK_BASE_URL`. Khi chạy Docker Compose, URL nội bộ là `http://mytasco-mock:8788`.

### User không thấy tài liệu mong đợi

Kiểm tra role, department, classification, alias phòng ban trong dataset và logic `core/rbac.py`.

### Thêm tool mới nhưng `/tools/openapi.json` chưa hiển thị

Cập nhật các nơi sau:

- `OPENAPI_SPEC` trong `app/agent/openapi_gateway.py`.
- `OpenAPIToolGateway.invoke()`.
- Tool wrapper trong `app/agent/tools.py`.
- Test tương ứng trong `tests/test_agent.py`.

## Contributing

Quy trình đề xuất:

1. Tạo branch từ `main`.
2. Cài dependencies cho service liên quan.
3. Viết/cập nhật test nếu thay đổi behavior.
4. Chạy test local:

```bash
cd services/orchestrator
pytest -v
```

5. Nếu đổi agent architecture, chạy thêm:

```bash
python test_structure.py
python demo_architecture.py
```

6. Mở pull request, mô tả rõ thay đổi, test đã chạy và rủi ro bảo mật/migration nếu có.

Guidelines:

- Giữ RBAC ở backend/tool layer, không chỉ dựa vào prompt.
- Không log secret, token, OTP hoặc dữ liệu lương.
- Ưu tiên pattern sẵn có trong repo.
- Với tool mới, cập nhật gateway, wrapper và test.
- Với schema dataset mới, cập nhật loader, ingestion và tài liệu.

## License

Chưa thấy file `LICENSE` trong repo hiện tại.

Khuyến nghị:

- Nếu là project nội bộ: thêm `Proprietary / Internal Use Only`.
- Nếu muốn open source: chọn license rõ ràng như MIT, Apache-2.0 hoặc BSD-3-Clause.

Cho đến khi có license chính thức, nên coi mã nguồn và dataset là tài sản nội bộ, không phân phối công khai.

## Acknowledgements

Project sử dụng hoặc tích hợp:

- FastAPI và Uvicorn.
- LangChain và LangGraph.
- OpenAI model qua `langchain-openai`.
- pandas, openpyxl và scikit-learn.
- Streamlit.
- httpx.
- Docker Compose, Qdrant và Postgres.
- Terraform và GitHub Actions.

Tài liệu liên quan:

- `docs/architecture.md`
- `docs/access-control.md`
- `docs/qa-examples.md`
- `ARCHITECTURE_IMPLEMENTATION.md`
- `SETUP_AND_DEPLOYMENT.md`
- `QUICK_REFERENCE.md`

