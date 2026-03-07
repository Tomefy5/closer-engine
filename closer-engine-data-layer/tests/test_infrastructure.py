import os
import pytest
import psycopg2
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv(".env.local")

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

@pytest.fixture
def supabase_client() -> Client:
    """Fixture pour le client Supabase Python (validation SDK)."""
    assert URL and KEY, "SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY doivent être définis dans .env.local"
    return create_client(URL, KEY)

@pytest.fixture
def db_connection():
    """Fixture de connexion PostgreSQL locale."""
    conn_string = "postgresql://postgres:postgres@127.0.0.1:54322/postgres"
    conn = psycopg2.connect(conn_string)
    yield conn
    conn.close()

def test_supabase_connection(supabase_client: Client, db_connection):
    """
    Test 1: Se connecte à Supabase local et fait un SELECT 1.
    """
    # Test via SDK (PostgREST HTTP validation basique en tapant /)
    # The simplest way to test python supabase client connection is calling a table
    # but we don't have tables. We'll rely on psycopg2 for the SELECT 1.
    with db_connection.cursor() as cur:
        cur.execute("SELECT 1;")
        result = cur.fetchone()
        assert result[0] == 1, "La connexion à PostgreSQL a échoué."

def test_pgvector_enabled(db_connection):
    """
    Test 2: Vérifie que l'extension vector est activée.
    """
    with db_connection.cursor() as cur:
        cur.execute("SELECT * FROM pg_extension WHERE extname = 'vector';")
        result = cur.fetchone()
        assert result is not None, "TDD Echec: L'extension 'vector' n'est pas encore activée."

def test_tables_exist(db_connection):
    """
    Test 3: Vérifie que les tables 'tenants', 'chat_sessions', et 'documents' existent 
    suite à la migration.
    """
    with db_connection.cursor() as cur:
        expected_tables = ["tenants", "chat_sessions", "documents"]
        for table in expected_tables:
            cur.execute(
                f"SELECT table_name FROM information_schema.tables "
                f"WHERE table_schema = 'public' AND table_name = '{table}'"
            )
            result = cur.fetchone()
            assert result is not None, f"TDD Echec: La table '{table}' n'existe pas."

