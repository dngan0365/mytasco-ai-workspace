from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.data.loader import get_store
from app.routers import auth, chat, documents, evaluation, search, staff, tools


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Nạp dataset + build TF-IDF index 1 lần, tránh mỗi request phải đọc lại xlsx
    get_store()
    yield


app = FastAPI(
    title="My Tasco AI Workspace",
    description="Enterprise Knowledge & Secure AI Search cho My Tasco (hackathon build)",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/health", tags=["system"])
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(documents.router)
app.include_router(search.router)
app.include_router(chat.router)
app.include_router(tools.router)
app.include_router(evaluation.router)
app.include_router(staff.router)
