"""Tests unitaires pour le routeur Webhook Meta."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch

from app.main import app

client = TestClient(app)


@pytest.fixture
def mock_meta_settings():
    """Fixture pour mocker les paramètres Meta du webhook."""
    with patch("app.api.webhooks.meta.settings") as mocked_settings:
        mocked_settings.META_VERIFY_TOKEN = "secret_verify_token"
        yield mocked_settings


def test_meta_webhook_verification_success(mock_meta_settings) -> None:
    """Vérifie que la vérification du webhook Meta réussit avec le bon token.
    
    Simule une requête GET valide de Meta.
    """
    verify_token = "secret_verify_token"
    challenge = "challenge_123"
    
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": verify_token,
            "hub.challenge": challenge,
        },
    )

    assert response.status_code == 200
    assert response.text == challenge


def test_meta_webhook_verification_failure(mock_meta_settings) -> None:
    """Vérifie que la vérification du webhook Meta échoue avec un mauvais token.
    
    Simule une requête GET avec un verify_token invalide.
    """
    response = client.get(
        "/webhook",
        params={
            "hub.mode": "subscribe",
            "hub.verify_token": "invalid_token",
            "hub.challenge": "challenge_123",
        },
    )

    assert response.status_code == 403


def test_meta_webhook_receive_payload() -> None:
    """Vérifie que la réception d'un payload Meta retourne HTTP 200.
    
    Simule l'envoi d'un POST basique représentant un événement WhatsApp.
    """
    payload = {
        "object": "whatsapp_business_account",
        "entry": [
            {
                "id": "WHATSAPP_BUSINESS_ACCOUNT_ID",
                "changes": [
                    {
                        "value": {
                            "messaging_product": "whatsapp",
                            "metadata": {
                                "display_phone_number": "PHONE_NUMBER",
                                "phone_number_id": "PHONE_NUMBER_ID"
                            },
                            "messages": [
                                {
                                    "from": "SENDER_PHONE_NUMBER",
                                    "id": "MESSAGE_ID",
                                    "timestamp": "TIMESTAMP",
                                    "text": {
                                        "body": "MESSAGE_BODY"
                                    },
                                    "type": "text"
                                }
                            ]
                        },
                        "field": "messages"
                    }
                ]
            }
        ]
    }
    
    response = client.post("/webhook", json=payload)

    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
