# Closer Engine

**Closer Engine** est un Agent IA conversationnel WhatsApp B2B multi-tenant, construit avec FastAPI, Python et Supabase.

## Architecture - Flux de traitement d'un message WhatsApp

Le système est conçu pour répondre instantanément aux Webhooks de Meta afin d'éviter les timeouts et les retransmissions, tout en déléguant le traitement IA lourd en arrière-plan.

```text
[Meta Webhook] -> (Payload JSON) -> [FastAPI POST /webhook]
                                            |
                                    [200 OK immédiat] <- (Évite les retransmissions)
                                            |
                                [BackgroundTask Worker] -> (process_whatsapp_message)
                                            |
                                  [Extraction du texte] <- (Gestion robuste des erreurs)
                                            |
                              [TODO: LangGraph Agent - Jour 3]
```

1. **Meta Webhook** : Meta Cloud API envoie un événement lors de la réception d'un message sur WhatsApp Business.
2. **FastAPI POST /webhook** : La route de l'application reçoit le JSON.
3. **200 OK immédiat** : FastAPI accuse réception (`{"status": "ok"}`) sous 200ms à l'API Meta.
4. **BackgroundTask Worker** : Simultanément, la tâche de fond (`process_whatsapp_message`) prend le relais.
5. **Extraction du texte** : Le worker extrait de manière sécurisée les éléments nécessaires depuis la hiérarchie complexe Meta (`entry -> changes -> value -> messages -> text -> body`).
6. **LangGraph Agent** : *(Prochaine étape)* Le texte extrait est transmis à l'Agent IA pour analyse et réponse.
