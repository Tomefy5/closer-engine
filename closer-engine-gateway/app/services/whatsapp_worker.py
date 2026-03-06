"""Service de traitement asynchrone des messages WhatsApp en arrière-plan."""

import logging
from typing import Any

logger: logging.Logger = logging.getLogger(__name__)


async def process_whatsapp_message(payload: dict[str, Any]) -> None:
    """Traite un message WhatsApp entrant en arrière-plan.

    Extrait le texte du message depuis le payload Meta de manière sécurisée.
    Gère les erreurs pour s'assurer que le traitement en arrière-plan
    ne plante jamais silencieusement.

    Args:
        payload (dict[str, Any]): Le payload brut JSON provenant du webhook Meta.

    Returns:
        None

    Raises:
        Aucune exception n'est levée (toutes les erreurs sont capturées et logguées).
    """
    logger.info("Début du traitement asynchrone du message WhatsApp...")

    try:
        # 1. Le payload WhatsApp est groupé par "entries" (généralement une seule pour un message)
        entries = payload.get("entry", [])
        if not entries:
            logger.warning("⚠️ Payload reçu non-textuel, ignoré (pas d'entry).")
            return

        # 2. Chaque entry contient une liste de "changes" correspondants à l'événement
        changes = entries[0].get("changes", [])
        if not changes:
            logger.warning("⚠️ Payload reçu non-textuel, ignoré (pas de changes).")
            return

        # 3. La valeur utile (le message ou le statut) se trouve dans "value"
        value = changes[0].get("value", {})
        
        # 4. On extrait la liste de messages depuis "value" (absent si c'est un accusé de réception)
        messages = value.get("messages", [])
        if not messages:
            logger.warning("⚠️ Payload reçu non-textuel, ignoré (pas de messages).")
            return

        # 5. On analyse le premier (et généralement unique) message
        message = messages[0]
        message_type = message.get("type")

        # 6. Ce MVP Sprint 1 ne traite que les messages de type "text"
        if message_type != "text":
            logger.warning("⚠️ Payload reçu non-textuel, ignoré (type: %s).", message_type)
            return

        # 7. Extraction du corps du texte et de l'expéditeur
        text_body = message.get("text", {}).get("body")
        sender_phone = message.get("from")

        if text_body and sender_phone:
            logger.info("📩 Message reçu de %s : %s", sender_phone, text_body)
            # TODO: Jour 3 - Appeler LangGraph ici avec le message extrait.
        else:
            logger.warning("⚠️ Payload reçu non-textuel, ignoré (corps de texte manquant).")

    except Exception:
        # Bloc catch-all final exhaustif : garantit que BackgroundTasks FastAPI n'échoue
        # pas brutalement en tâche de fond en cas de KeyError / IndexError non prévu ou payload exotique.
        logger.exception("Erreur inattendue lors du traitement du message WhatsApp.")
    finally:
        logger.info("Fin du traitement asynchrone du message WhatsApp.")
