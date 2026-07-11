# Setup & Deployment Guide

## ✅ Current Status

The My Tasco AI Workspace has been successfully updated to the new LangGraph-based architecture:

- ✅ **Intent Router**: Routes queries to RAG, Tool, or Human Approval handlers
- ✅ **OpenAPI Gateway**: Provides enterprise tool discovery and mocking
- ✅ **Guardrails**: Checks output for PII and sensitive data
- ✅ **Permission-Aware Tools**: All tool access respects user RBAC
- ✅ **Backward Compatible**: Existing `/chat/ask` endpoint works with new architecture

**Demo Status**: `python demo_architecture.py` runs successfully showing all routing paths working.

---

## 📦 Installation Steps

### Prerequisites
- Python 3.10+
- pip 24.0+
- Virtual environment (recommended)

### Step 1: Create Virtual Environment (Optional but Recommended)
```bash
cd c:\Users\mt200\OneDrive\Desktop\mytasco-ai-workspace

# Create virtual environment
python -m venv .venv

# Activate it
# On Windows:
.\.venv\Scripts\Activate.ps1
# On macOS/Linux:
source .venv/bin/activate
```

### Step 2: Install Dependencies

```bash
cd services/orchestrator

# Install core dependencies
pip install --upgrade pip setuptools wheel
pip install -r requirements-core.txt

# Install my-tasco-adapter (handles pyproject.toml)
pip install ../mytasco-adapter

# Install remaining test dependencies
pip install pytest pytest-asyncio
```

### Step 3: Verify Installation

```bash
# Test structure (no external deps)
python test_structure.py

# Test imports (requires all dependencies)
python test_imports.py

# Run demo
python demo_architecture.py
```

### Step 4: Configure Environment

Create `.env` file in `services/orchestrator/`:
```
OPENAI_API_KEY=sk-...  # Get from OpenAI platform
DATASET_PATH=app/data/ai_workspace_dataset_vietnamese_participants.xlsx
DATABASE_URL=sqlite:///./data/mytasco.db  # Optional
```

### Step 5: Run Existing Tests

```bash
cd services/orchestrator

# Run all tests
pytest tests/ -v

# Run specific test suite
pytest tests/test_agent.py -v
pytest tests/test_api.py -v
pytest tests/test_rbac.py -v
```

### Step 6: Start Backend Server

```bash
cd services/orchestrator

# Development mode with auto-reload
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## 🧪 Testing the API

### 1. Get OpenAPI Gateway Spec
```bash
curl http://localhost:8000/tools/openapi.json | python -m json.tool
```

Response shows 6 available operations:
- search_staff_directory
- list_hr_requests
- get_staff_attendance
- get_payslip
- search_company_news
- search_notifications

### 2. Health Check
```bash
curl http://localhost:8000/health
# {"status": "ok"}
```

### 3. Chat with Intent Routing

#### RAG Query (Policy/Document)
```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Quy chế nội bộ của công ty là gì?"
  }'
```

#### Tool Query (HR/Business Data)
```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Xem chấm công tháng này"
  }'
```

#### Human Approval Query
```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..." \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Phê duyệt đơn xin nghỉ phép của nhân viên này"
  }'
```

### 4. Test Individual Tools

#### Search Staff Directory
```bash
curl -X POST http://localhost:8000/chat/ask \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "question": "Tìm kiếm nhân viên tên Nguyễn"
  }'
```

Expected Response:
```json
{
  "answer": "...",
  "sources": [],
  "mode": "tool-agent",
  "intent": "tool"
}
```

---

## 🏗️ Architecture Components

### Request Flow

```
┌─────────────────────────────────────────────────────────────┐
│  1. User Question via /chat/ask                             │
└────────────────┬────────────────────────────────────────────┘
                 │
                 ▼
        ┌─────────────────────┐
        │  Intent Router      │
        │  (app/agent/router) │
        └──┬──────────────┬───┘
           │              │
      ┌────▼────┐    ┌────▼─────┐    ┌──────────────┐
      │   RAG   │    │   TOOL    │    │ HUMAN APPROV │
      │  Intent │    │  Intent   │    │    INTENT    │
      └────┬────┘    └────┬─────┘    └──────┬───────┘
           │              │                  │
           ▼              ▼                  ▼
    ┌─────────────┐ ┌─────────────────┐ ┌─────────────┐
    │ Knowledge   │ │  OpenAPI        │ │  Human      │
    │ Base Search │ │  Tool Gateway   │ │  Queue      │
    │ (RBAC)      │ │  (6 operations) │ │             │
    └──────┬──────┘ └────────┬────────┘ └──────┬──────┘
           │                 │                 │
           └────────┬────────┴────────┬────────┘
                    │                │
                    ▼                ▼
            ┌──────────────────┐  ┌─────────────┐
            │    Guardrails    │  │    Format   │
            │  (PII checking)  │  │  Response   │
            └────────┬─────────┘  └─────────────┘
                     │
                     ▼
            ┌──────────────────┐
            │   /chat/ask      │
            │   Response       │
            └──────────────────┘
```

### Key Modules

| Module | Purpose | Status |
|--------|---------|--------|
| `router.py` | Intent classification | ✅ Complete |
| `openapi_gateway.py` | Tool discovery & mocking | ✅ Complete |
| `graph.py` | LangGraph orchestration | ✅ Complete |
| `tools.py` | LangChain tool definitions | ✅ Complete |
| `knowledge_base.py` | TF-IDF retriever | ✅ Complete |
| `chat.py` | Updated endpoint router | ✅ Complete |

---

## 🔐 Security Considerations

### 1. Authentication
- JWT tokens required for all endpoints
- Token validation in `core/security.py`
- Token includes user identity and role

### 2. Authorization (RBAC)
- All knowledge base queries filtered by `core/rbac.py`
- Tool access checked before returning any data
- User role determines accessible documents/tools

### 3. Guardrails
- Output checked for PII before returning to user
- Patterns checked: SSN, credit card numbers, passwords
- Blocks response if sensitive data detected

### 4. Data Sensitivity
- Payslip access requires OTP (step-up auth)
- All sensitive queries logged for audit trail
- Tool responses scrubbed of direct employee data

---

## 📊 Monitoring

### Logs to Monitor

```bash
# Watch application logs
tail -f logs/app.log

# Check error rates
grep ERROR logs/app.log | wc -l

# Monitor tool gateway failures
grep "gateway.invoke" logs/app.log
```

### Metrics to Track

1. **Intent Distribution**
   - RAG queries: %
   - Tool queries: %
   - Approval requests: %

2. **Tool Performance**
   - Tool gateway response time
   - Staff directory search latency
   - Payslip generation time

3. **Security**
   - Guardrail blocks per day
   - Failed authentication attempts
   - Unauthorized access attempts

---

## 🚀 Production Deployment

### Prerequisites
- Docker (for containerization)
- Kubernetes cluster (optional, for orchestration)
- PostgreSQL (recommended for production)
- Redis (optional, for caching)

### Docker Deployment

```dockerfile
# Use official Python runtime
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY services/orchestrator/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY services/orchestrator/app ./app

# Expose port
EXPOSE 8000

# Start application
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Kubernetes Deployment

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: mytasco-orchestrator
spec:
  replicas: 3
  selector:
    matchLabels:
      app: mytasco-orchestrator
  template:
    metadata:
      labels:
        app: mytasco-orchestrator
    spec:
      containers:
      - name: orchestrator
        image: mytasco-orchestrator:latest
        ports:
        - containerPort: 8000
        env:
        - name: OPENAI_API_KEY
          valueFrom:
            secretKeyRef:
              name: api-keys
              key: openai
        livenessProbe:
          httpGet:
            path: /health
            port: 8000
          initialDelaySeconds: 30
          periodSeconds: 10
```

---

## 🆘 Troubleshooting

### Issue: "ModuleNotFoundError: No module named 'langchain_openai'"

**Solution**: Install missing dependencies
```bash
pip install langchain-openai
```

### Issue: "OPENAI_API_KEY not set"

**Solution**: Set in environment
```bash
export OPENAI_API_KEY=sk-...
# or in .env
echo "OPENAI_API_KEY=sk-..." > .env
```

### Issue: "Intent router always returns RAG"

**Solution**: Check keywords in router.py match your queries
```python
# Add more keywords if needed
_TOOL_HINTS += ("your-keyword",)
```

### Issue: "Tool gateway returns mock data in production"

**Reason**: MyTascoClient not available
**Solution**: Ensure mytasco-adapter is installed and configured
```bash
pip install ../mytasco-adapter
```

---

## 📚 Further Reading

- [LangGraph Documentation](https://langchain-ai.github.io/langgraph/)
- [LangChain Tools](https://python.langchain.com/docs/modules/tools/)
- [FastAPI](https://fastapi.tiangolo.com/)
- [OpenAPI Specification](https://swagger.io/specification/)

---

## 🎯 Next Steps

1. **Install Dependencies**: Follow Step 1-3 above
2. **Configure Environment**: Create `.env` with API keys
3. **Run Tests**: Verify everything works with `pytest tests/`
4. **Start Server**: `uvicorn app.main:app --reload`
5. **Test Endpoints**: Use curl examples to verify
6. **Monitor**: Set up logging and metrics collection
7. **Deploy**: Use Docker/Kubernetes for production

---

## 💬 Support

For issues or questions:
1. Check the ARCHITECTURE_IMPLEMENTATION.md for architecture details
2. Run `python demo_architecture.py` to see current flow
3. Check test files in `tests/` for usage examples
4. Review docstrings in source files for detailed explanations

---

**Last Updated**: 2025-01-09  
**Status**: Production Ready (Pending Dependency Installation)


