"""Routeur pour les webhooks Meta (WhatsApp Business API)."""

from fastapi import APIRouter

router: APIRouter = APIRouter(
    prefix="/webhooks/meta",
    tags=["Webhooks Meta"],
)


# TODO: Implémenter la vérification du webhook GET /webhooks/meta
# TODO: Implémenter la réception des messages POST /webhooks/meta
