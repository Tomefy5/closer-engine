import pytest
from unittest.mock import MagicMock
from langchain_core.documents import Document

# On mocke l'import des futures fonctions pour que les tests puissent s'exécuter
# Même si le fichier scripts/ingest_rag n'existe pas encore, on peut le créer
# à vide pour lancer pytest, ou importer depuis un module qui existe.
# Pour le vrai TDD, le fichier ingest_rag n'existe pas, donc l'import échouerait.
# On va créer le squelette des fonctions dans le test s'il n'existe pas encore
# puis on l'importera depuis scripts.ingest_rag.
try:
    from scripts.ingest_rag import load_and_chunk_pdf, vectorize_text, upsert_documents
except ImportError:
    # Pour permettre à pytest de s'exécuter et de montrer l'échec (RED)
    # plutot que de planter bêtement sur ImportError
    def load_and_chunk_pdf(file_path): raise NotImplementedError()
    def vectorize_text(embeddings, text): raise NotImplementedError()
    def upsert_documents(client, tenant_id, chunks): raise NotImplementedError()


def test_pdf_loader_splits_chunks(mocker):
    """Vérifie que load_and_chunk_pdf décompose un PDF en chunks de texte."""
    # Mocking PyPDFLoader pour ne pas avoir besoin de lire de vrai fichier
    mock_loader = mocker.patch("scripts.ingest_rag.PyPDFLoader", create=True)
    
    # On mocke le load() pour retourner un "document" brut qui sera ensuite splitté
    # par le RecursiveCharacterTextSplitter dans l'implémentation.
    mock_document = Document(page_content="Un long texte hypothétique pour simuler un PDF de plusieurs pages avec des tarifs B2B.")
    mock_loader.return_value.load.return_value = [mock_document]
    
    # On mocke également le RecursiveCharacterTextSplitter pour s'assurer
    # qu'il renvoie bien 3 documents découpés
    mock_splitter = mocker.patch("scripts.ingest_rag.RecursiveCharacterTextSplitter", create=True)
    mock_chunks = [
        Document(page_content="Chunk 1"),
        Document(page_content="Chunk 2"), 
        Document(page_content="Chunk 3")
    ]
    mock_splitter.return_value.split_documents.return_value = mock_chunks

    # Exécution de la fonction
    result = load_and_chunk_pdf("dummy_path.pdf")
    
    # Assertions
    assert isinstance(result, list)
    assert len(result) >= 3 and len(result) <= 5
    assert all(isinstance(doc, Document) for doc in result)


def test_embeddings_shape(mocker):
    """Vérifie que vectorize_text retourne bien un vecteur 1536 float."""
    # Création d'un mock pour OpenAIEmbeddings
    mock_embeddings = MagicMock()
    # On simule le retour d'un vecteur de 1536 flottants
    mock_embeddings.embed_query.return_value = [0.1] * 1536
    
    result = vectorize_text(mock_embeddings, "Test text")
    
    assert isinstance(result, list)
    assert len(result) == 1536
    assert isinstance(result[0], float)
    mock_embeddings.embed_query.assert_called_once_with("Test text")


def test_supabase_insert_success(mocker, monkeypatch):
    """Vérifie que upsert_documents appelle bien insert sur la table documents."""
    # Simuler la clé API pour OpenAIEmbeddings qui est instanciée dans upsert_documents
    monkeypatch.setenv("OPENAI_API_KEY", "sk-mock-demo-key-for-local-testing")

    mock_client = MagicMock()
    mock_table = mock_client.table.return_value
    mock_insert = mock_table.insert.return_value
    mock_insert.execute.return_value = {"data": [{"id": 1}]}

    tenant_id = "123e4567-e89b-12d3-a456-426614174000"
    chunks = [
        Document(page_content="Mon texte", metadata={"source": "doc1"}),
    ]

    # Note: L'implémentation devra intégrer directement le mock_embeddings dans la vraie boucle,
    # ou vectorize_text. Ici on mock vectorize_text
    mocker.patch("scripts.ingest_rag.vectorize_text", return_value=[0.1]*1536, create=True)

    upsert_documents(mock_client, tenant_id, chunks)

    # Vérification que .table() a bien été appelé sur 'documents'
    mock_client.table.assert_called_with("documents")
    # Vérification que .insert() a bien été appelé avec des arguments contenant le tenant_id
    # L'argument passé à insert() est une liste de dictionnaires (records)
    insert_args = mock_table.insert.call_args[0][0] # list of records
    first_record = insert_args[0]
    
    assert "tenant_id" in first_record
    assert first_record["tenant_id"] == tenant_id
    assert "content" in first_record
    assert first_record["content"] == "Mon texte"
    assert "metadata" in first_record
    assert "embedding" in first_record
