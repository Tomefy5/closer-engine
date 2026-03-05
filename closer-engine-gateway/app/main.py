"""Point d'entrée principal de l'application Closer Engine."""

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from app.core.config import settings

app: FastAPI = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Agent IA WhatsApp B2B — Closer Engine",
    docs_url="/docs",
    redoc_url="/redoc",
)


@app.get(
    "/",
    summary="Vérification de santé",
    tags=["Santé"],
    response_class=JSONResponse,
)
async def health_check() -> dict[str, str]:
    """Endpoint de santé de l'application.

    Permet de vérifier que le service est opérationnel.

    Returns:
        dict[str, str]: Un dictionnaire contenant le statut et le nom du service.
    """
    return {"status": "ok", "service": settings.APP_NAME}
