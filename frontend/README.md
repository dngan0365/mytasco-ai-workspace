# My Tasco AI Workspace frontend

Next.js App Router frontend for the FastAPI orchestrator in `services/orchestrator`.

## Run

```bash
cd frontend
cp .env.example .env.local
npm install
npm run dev
```

Set `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`. Start the backend separately on port 8000.

The current backend implements login, document reads, search, and chat. The frontend also contains create, update, and delete service methods and screens; those mutations require corresponding backend endpoints (`POST /documents`, `PUT /documents/{id}`, and `DELETE /documents/{id}`).
