"""Routeur pour les webhooks Meta (WhatsApp Business API).

Ce module expose deux routes sur l'endpoint /webhook :
- GET  /webhook : vérification d'abonnement par Meta
- POST /webhook : réception des messages et événements WhatsApp
"""

import logging
from typing import Any

from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from fastapi.responses import PlainTextResponse

from app.core.config import settings
from app.services.whatsapp_worker import process_whatsapp_message

logger: logging.Logger = logging.getLogger(__name__)

router: APIRouter = APIRouter(
    prefix="/webhook",
    tags=["Webhooks Meta"],
)


@router.get(
    "",
    summary="Vérification du webhook Meta",
    response_class=PlainTextResponse,
    status_code=200,
)
async def verify_webhook(
    hub_mode: str = Query(alias="hub.mode", description="Mode envoyé par Meta"),
    hub_verify_token: str = Query(
        alias="hub.verify_token", description="Token de vérification envoyé par Meta"
    ),
    hub_challenge: str = Query(
        alias="hub.challenge", description="Défi à renvoyer pour confirmer l'abonnement"
    ),
) -> str:
    """Vérifie l'abonnement au webhook Meta (WhatsApp Business API).

    Meta envoie une requête GET lors de la configuration du webhook pour s'assurer
    que le serveur est bien le propriétaire de l'endpoint. Si le token correspond,
    on renvoie le challenge en texte brut pour confirmer l'abonnement.

    Args:
        hub_mode: Doit être "subscribe" pour valider la vérification.
        hub_verify_token: Token envoyé par Meta, doit correspondre à META_VERIFY_TOKEN.
        hub_challenge: Valeur fournie par Meta à renvoyer telle quelle.

    Returns:
        str: La valeur exacte de hub.challenge en texte brut (requis par Meta).

    Raises:
        HTTPException: 403 si le mode ou le token ne correspondent pas.
    """
    if hub_mode != "subscribe" or hub_verify_token != settings.META_VERIFY_TOKEN:
        logger.warning(
            "Tentative de vérification webhook échouée — mode=%s token_valid=%s",
            hub_mode,
            hub_verify_token == settings.META_VERIFY_TOKEN,
        )
        raise HTTPException(status_code=403, detail="Vérification du webhook refusée.")

    logger.info("Webhook Meta vérifié avec succès — challenge=%s", hub_challenge)
    return hub_challenge


@router.post(
    "",
    summary="Réception des messages WhatsApp",
    status_code=200,
)
async def receive_message(
    payload: dict[str, Any],
    background_tasks: BackgroundTasks,
) -> dict[str, str]:
    """Reçoit et accuse réception des événements WhatsApp envoyés par Meta.

    Meta exige une réponse HTTP 200 immédiate (sous 20 secondes) pour éviter
    les retransmissions. Le traitement asynchrone du message est délégué
    à un worker en arrière-plan (BackgroundTasks).

    Args:
        payload: Corps JSON brut de la notification Meta (messages, statuts, etc.).
        background_tasks: Injecteur FastAPI pour l'exécution asynchrone hors requête.

    Returns:
        dict[str, str]: Accusé de réception immédiat {"status": "ok"}.
    """
    logger.info("Payload WhatsApp reçu, délégation en arrière-plan...")
    
    # Délégation du vrai traitement pour répondre en < 200ms
    background_tasks.add_task(process_whatsapp_message, payload)
    
    return {"status": "ok"}
