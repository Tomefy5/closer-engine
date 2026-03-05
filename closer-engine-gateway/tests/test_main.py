"""Tests unitaires pour le module principal de l'application."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app


@pytest.mark.anyio
async def test_health_check_status_200() -> None:
    """Vérifie que l'endpoint de santé retourne bien un statut HTTP 200.

    Assure que la route GET / est opérationnelle et accessible.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/")

    assert response.status_code == 200


@pytest.mark.anyio
async def test_health_check_response_body() -> None:
    """Vérifie que l'endpoint de santé retourne le corps JSON attendu.

    Le corps de la réponse doit contenir les clés 'status' et 'service'.
    """
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://testserver",
    ) as client:
        response = await client.get("/")

    data: dict[str, str] = response.json()
    assert data["status"] == "ok"
    assert "service" in data
