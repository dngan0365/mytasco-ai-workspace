# Build context PHAI la thu muc goc repo (mytasco-ai-workspace/), vi service nay
# phu thuoc package cuc bo services/mytasco-adapter.
# Vi du: docker build -f services/orchestrator/Dockerfile -t orchestrator .

FROM python:3.11-slim
WORKDIR /app

COPY services/mytasco-adapter /app/services/mytasco-adapter
COPY services/orchestrator/requirements.txt /app/services/orchestrator/requirements.txt

WORKDIR /app/services/orchestrator
RUN pip install --no-cache-dir -r requirements.txt /app/services/mytasco-adapter

COPY services/orchestrator /app/services/orchestrator

EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
