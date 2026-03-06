"""Tests TDD pour implémenter le traitement asynchrone des webhooks Meta.

Jour 2 : Vérification du routage en arrière-plan (FastAPI BackgroundTasks).
"""

import time
import asyncio
from unittest.mock import patch, AsyncMock
import pytest
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


@pytest.fixture
def sample_whatsapp_payload() -> dict:
    """Fixture retournant un payload mocké d'un message entrant WhatsApp."""
    return {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "123456789",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "messages": [
                                {
                                    "from": "33612345678",
                                    "id": "wamid.HBgL...",
                                    "timestamp": "1710000000",
                                    "text": {"body": "Bonjour, je voudrais tester !"},
                                    "type": "text",
                                }
                            ],
                        },
                        "field": "messages",
                    }
                ],
            }
        ],
    }


def test_webhook_returns_200_immediately(sample_whatsapp_payload: dict) -> None:
    """Vérifie que la route POST ranvoie un HTTP 200 avec {"status": "ok"} immédiatement.
    
    Ce fonctionnement est obligatoire pour éviter que Meta n'abandonne la requête (timeout).
    """
    response = client.post("/webhook", json=sample_whatsapp_payload)
    
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


@patch("app.api.webhooks.meta.process_whatsapp_message", create=True)
def test_background_task_is_triggered(mock_worker, sample_whatsapp_payload: dict) -> None:
    """Vérifie que la fonction worker (process_whatsapp_message) est appelée en background.
    
    Un objet mock vérifie que le routage passe bien le payload exact reçu
    à cette méthode asynchrone pour un traitement ultérieur.
    """
    response = client.post("/webhook", json=sample_whatsapp_payload)
    
    assert response.status_code == 200
    # On valide que FastAPI ou notre logique a redirigé le message au worker
    mock_worker.assert_called_once_with(sample_whatsapp_payload)


@pytest.mark.asyncio
async def test_webhook_response_does_not_wait_for_worker(sample_whatsapp_payload: dict) -> None:
    """Vérifie que la réponse de l'API HTTP 200 ne bloque pas sur le traitement du message.
    
    Nous mockons un worker très lent (5 secondes). Le test vérifie que la requête 
    POST est toujours renvoyée en une fraction de seconde, prouvant la nature asynchrone.
    """
    import uvicorn
    import threading
    import httpx
    from unittest.mock import patch, AsyncMock
    
    # Configuration du serveur
    port = 8124
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="critical")
    server = uvicorn.Server(config)
    
    # Thread pour faire tourner le serveur en arrière-plan
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    
    # Attendre que le serveur soit prêt
    while not server.started:
        await asyncio.sleep(0.1)

    try:
        # On patche le worker DANS le test, cela s'applique au serveur ASGI en cours car il
        # tourne dans le même processus (thread différent mais même espace mémoire).
        with patch("app.api.webhooks.meta.process_whatsapp_message", new_callable=AsyncMock) as mock_worker:
            async def slow_worker_simulator(payload):
                await asyncio.sleep(5.0)

            mock_worker.side_effect = slow_worker_simulator

            start_time = time.time()
            
            # Utilisation de httpx (vrai client HTTP réseau) pour prouver le non-blocage
            with httpx.Client() as sync_client:
                response = sync_client.post(f"http://127.0.0.1:{port}/webhook", json=sample_whatsapp_payload)
            
            end_time = time.time()
            elapsed_time = end_time - start_time
            
            assert response.status_code == 200
            # Le temps total de l'échange HTTP doit demeurer minime
            assert elapsed_time < 1.0, f"Erreur, la requête s'est bloquée pdt {elapsed_time:.2f}s."
            
            # Vérifier que le worker a bien été appelé (il est parti tourner pendant 5s)
            
            # Note: pour AsyncMock, la vérification peut être plus capricieuse en multithreading.
            # Normalement assert_called_once passe ici.
            mock_worker.assert_called_once()
            
            # On annule explicitement les tâches en cours du serveur pour fermer le test proprement
            server.should_exit = True
    finally:
        server.should_exit = True
        thread.join(timeout=2)
