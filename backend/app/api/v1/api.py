from fastapi import APIRouter
from app.api.v1.endpoints import invoices, settings, webhooks

api_router = APIRouter()

api_router.include_router(invoices.router, prefix="/invoices", tags=["Invoices"])
api_router.include_router(settings.router, prefix="/settings", tags=["Settings"])
api_router.include_router(webhooks.router, prefix="/webhooks", tags=["Webhooks"])

@api_router.get("/health")
def api_v1_health():
    return {"status": "ok", "version": "v1"}
