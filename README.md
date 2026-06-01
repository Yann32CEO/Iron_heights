# Iron Heights V2

Iron Heights V2 is a multi-phase security lab with an Angular frontend, a FastAPI backend, and PostgreSQL state.

## Deployment

1. Copy .env.example to .env.
2. Replace the placeholder database password, challenge secrets, flags, and public origin values.
3. Start the production compose stack:

~~~bash
docker compose up --build -d
~~~

The frontend listens on port 4000 and proxies API traffic to the backend service.

## Configuration Notes

- CORS_ALLOW_ORIGINS and FRONTEND_ALLOWED_ORIGINS must match the public lab origin when deployed behind a domain.
- JWT_SECRET, PHASE3_JWT_SECRET, and PHASE3_AES_PASSWORD are part of the Phase 3 challenge path and must stay aligned with the in-game clues.
- ARTEMIS_OLLAMA_ENABLED=false can be used when no Ollama endpoint is available.
- The PostgreSQL data volume is configured in docker-compose.yml; adjust it for the production host before deploying.

## Development

The service Dockerfiles still include development targets for local work. The default compose file uses production targets.
