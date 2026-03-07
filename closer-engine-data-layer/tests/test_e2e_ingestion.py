import os
import pytest
from supabase import create_client, Client
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv(".env.local")

URL = os.environ.get("SUPABASE_URL")
KEY = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")

@pytest.fixture
def supabase_client() -> Client:
    """Fixture retournant le client de la DB locale (real DB)."""
    assert URL and KEY, "SUPABASE_URL et SUPABASE_SERVICE_ROLE_KEY manquants."
    return create_client(URL, KEY)

def test_e2e_ingestion_database_insert(supabase_client: Client):
    """
    Test E2E :
    1. Crée un tenant de test réel.
    2. Insère un seul document (chunk) comprenant du texte et un vecteur mock en BDD.
    3. Exécute un SELECT et vérifie que l'enregistrement existe avec un vecteur non-nul.
    """
    
    # ÉTAPE 1 : Création du tenant
    tenant_res = supabase_client.table("tenants").insert({
        "company_name": "Test E2E RAG",
        "whatsapp_number_id": "test_e2e",
        "system_prompt": "Test"
    }).execute()
    
    assert tenant_res.data, "Impossible de créer le tenant de test."
    tenant_id = tenant_res.data[0]["id"]
    
    # ÉTAPE 2 : Insertion d'un document (chunk mock) dans la BD locale
    mocked_vector = [0.0123] * 1536 # Un vecteur artificiel de dimension 1536
    
    doc_res = supabase_client.table("documents").insert({
        "tenant_id": tenant_id,
        "content": "Ceci est un test E2E de pipeline RAG. Les tarifs sont factices.",
        "metadata": {"source": "e2e_test"},
        "embedding": mocked_vector
    }).execute()
    
    assert doc_res.data, "Erreur lors de l'insertion dans la table documents"
    inserted_doc_id = doc_res.data[0]["id"]
    
    # ÉTAPE 3 : Vérification (Select)
    verify_res = supabase_client.table("documents").select("*").eq("id", inserted_doc_id).execute()
    
    assert verify_res.data
    record = verify_res.data[0]
    
    assert record["content"] == "Ceci est un test E2E de pipeline RAG. Les tarifs sont factices."
    assert record["tenant_id"] == tenant_id
    assert "embedding" in record
    
    # Le vecteur retourné par Supabase est représenté en Python sous forme de string '[0.0123,...]' ou liste
    embedding_val = record["embedding"]
    assert embedding_val is not None, "Le vecteur d'embedding ne doit pas être null"
    
    # Selon le client psycop2/supabase, ce format peut être retourné comme un str ou array
    if isinstance(embedding_val, str):
        # "[0.0123, 0.0123, ...]" => assure que ce nest pas vide
        assert len(embedding_val) > 10, "Le vecteur format string semble anormalement ou vide"
    elif isinstance(embedding_val, list):
        assert len(embedding_val) == 1536, "La dimension du vecteur récupéré est incorrecte"
        
    # Nettoyage de fin de test (on supprime le locataire avec ON DELETE CASCADE)
    supabase_client.table("tenants").delete().eq("id", tenant_id).execute()
