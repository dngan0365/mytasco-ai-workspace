from fastapi import APIRouter

from app.agent.openapi_gateway import get_openapi_spec

router = APIRouter(prefix="/tools", tags=["tool-gateway"])


@router.get("/openapi.json")
def openapi_manifest():
    """OpenAPI manifest cho enterprise tool gateway."""
    return get_openapi_spec()
