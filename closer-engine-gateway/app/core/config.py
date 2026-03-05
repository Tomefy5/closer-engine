"""Module de configuration centralisé via Pydantic v2 BaseSettings."""

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Paramètres de l'application chargés depuis les variables d'environnement."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
    )

    # Informations de l'application
    APP_NAME: str = Field(default="Closer Engine", description="Nom de l'application")
    APP_VERSION: str = Field(default="0.1.0", description="Version de l'application")
    DEBUG: bool = Field(default=False, description="Mode debug")

    # Tokens Meta / WhatsApp Business API
    META_VERIFY_TOKEN: str = Field(
        ...,
        description="Token de vérification pour le webhook Meta",
    )
    META_ACCESS_TOKEN: str = Field(
        ...,
        description="Token d'accès à l'API Meta (WhatsApp Business)",
    )


def get_settings() -> Settings:
    """Retourne une instance de la configuration de l'application.

    Returns:
        Settings: L'instance de configuration singleton.
    """
    return Settings()  # type: ignore[call-arg]


settings: Settings = get_settings()
