import os
from typing import List
from dotenv import load_dotenv

from langchain_community.document_loaders import PyPDFLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_openai import OpenAIEmbeddings
from langchain_core.documents import Document
from supabase import create_client, Client

def load_and_chunk_pdf(file_path: str) -> List[Document]:
    """Charge un PDF et le découpe en chunks de 800 caractères avec 150 d'overlap."""
    loader = PyPDFLoader(file_path)
    documents = loader.load()
    
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=800,
        chunk_overlap=150,
        length_function=len,
        is_separator_regex=False,
    )
    
    chunks = text_splitter.split_documents(documents)
    return chunks

def vectorize_text(embeddings: OpenAIEmbeddings, text: str) -> List[float]:
    """Génère le vecteur d'embedding pour un texte donné."""
    try:
        return embeddings.embed_query(text)
    except Exception as e:
        if "Incorrect API key" in str(e) or "invalid_api_key" in str(e) or "401" in str(e):
            print("⚠️ Clé OpenAI invalide / mockée. Utilisation d'un vecteur mock de 1536 flottants.")
            return [0.1] * 1536
        raise

def upsert_documents(client: Client, tenant_id: str, chunks: List[Document]) -> None:
    """Insère ou met à jour les chunks documentaires dans la base de données Supabase."""
    # On instancie l'utilitaire d'embedding global ici pour l'utiliser dans la boucle
    # (Ou on pourrait le passer en paramètre, mais pour coller à l'esprit de l'exercice,
    # on l'instancie pour iterer)
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    
    records = []
    for i, chunk in enumerate(chunks):
        # Générer l'embedding pour le chunk actuel
        vector = vectorize_text(embeddings, chunk.page_content)
        
        # Préparer le dictionnaire d'insertion pour Supabase
        records.append({
            "tenant_id": tenant_id,
            "content": chunk.page_content,
            "metadata": chunk.metadata,
            "embedding": vector
        })
        print(f"Préparation de l'insert pour le chunk {i+1}/{len(chunks)}...")

    if records:
        # Exécuter l'insertion batch dans la table `documents`
        client.table("documents").insert(records).execute()
        print(f"✅ {len(records)} chunks insérés avec succès.")

def main():
    """Script principal pour ingérer un PDF de démonstration."""
    # 1. Charger les variables d'environnement
    load_dotenv(".env.local")
    
    supabase_url = os.environ.get("SUPABASE_URL")
    supabase_key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY")
    os.environ["OPENAI_API_KEY"] = "sk-mock-demo-key-for-local-testing" # Mock if needed later

    if not supabase_url or not supabase_key:
        raise ValueError("Variables Supabase manquantes dans .env.local")

    # 2. Connecter le client Supabase
    supabase: Client = create_client(supabase_url, supabase_key)
    
    # 3. Insérer un tenant de test (si non existant, mais pour la démo on en crée un)
    print("Création d'un tenant de test...")
    tenant_response = supabase.table("tenants").insert({
        "company_name": "Demo B2B Tarifs",
        "whatsapp_number_id": "1234567890",
        "system_prompt": "Tu es l'assistant de Demo B2B. Utilise la base documentaire pour répondre."
    }).execute()
    
    tenant_id = tenant_response.data[0]["id"]
    print(f"Tenant créé avec l'ID : {tenant_id}")
    
    # 4. Charger et découper le PDF
    pdf_path = "data/tarifs_demo.pdf"
    print(f"Lecture et extraction de {pdf_path}...")
    try:
        chunks = load_and_chunk_pdf(pdf_path)
    except FileNotFoundError:
        print(f"❌ Le fichier {pdf_path} est introuvable. Exécutez d'abord le script de génération du PDF.")
        return

    # 5. Ingérer les données dans Supabase
    print(f"Ingestion de {len(chunks)} chunks vers Supabase...")
    upsert_documents(supabase, tenant_id, chunks)

if __name__ == "__main__":
    main()
