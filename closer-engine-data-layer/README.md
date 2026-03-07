# Closer Engine - Data Layer

Ce dossier contient l'infrastructure de la base de données et les scripts associés (notamment l'ingestion de données pour le RAG).

## Démarrage local

L'infrastructure s'appuie sur le CLI Supabase (qui orchestre les conteneurs Docker locaux).

1. S'assurer que Docker est lancé.
2. Démarrer les services Supabase :
   ```bash
   supabase start
   ```
3. (Si nécessaire) Appliquer les migrations pour s'assurer que le schéma de base est à jour :
   ```bash
   supabase migration up
   ```

*(Les clés d'API locales `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY` sont automatiquement disponibles une fois le conteneur démarré, et doivent être ajoutées au `.env.local`).*

## Schéma de données

Le modèle de données pour l'agent B2B inclut les locataires (`tenants`), l'historique des discussions (`chat_sessions`) et les vecteurs documentaires (`documents`).

```sql
CREATE EXTENSION IF NOT EXISTS vector WITH SCHEMA extensions;

CREATE TABLE IF NOT EXISTS public.tenants (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_name TEXT NOT NULL,
    whatsapp_number_id TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    created_at TIMESTAMPTZ DEFAULT now()
);

CREATE TABLE IF NOT EXISTS public.chat_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    prospect_phone TEXT NOT NULL,
    session_status TEXT NOT NULL DEFAULT 'active',
    history JSONB NOT NULL DEFAULT '[]'::jsonb,
    updated_at TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX idx_chat_sessions_lookup ON public.chat_sessions(tenant_id, prospect_phone);

CREATE TABLE IF NOT EXISTS public.documents (
    id BIGSERIAL PRIMARY KEY,
    tenant_id UUID REFERENCES public.tenants(id) ON DELETE CASCADE,
    content TEXT NOT NULL,
    metadata JSONB DEFAULT '{}'::jsonb,
    embedding vector(1536)
);
CREATE INDEX idx_documents_embedding ON public.documents USING hnsw (embedding vector_cosine_ops);
```

## Ingestion RAG

Pour ingérer un document PDF dans la base de données vectorielles (table `documents`), assurez-vous que `OPENAI_API_KEY`, `SUPABASE_URL` et `SUPABASE_SERVICE_ROLE_KEY` sont renseignées dans `.env.local` puis lancez le script python :

```bash
uv run python scripts/ingest_rag.py
```
