# Nexa Infrastructure Foundation

Shared, domain-neutral infrastructure for HTTP delivery, PostgreSQL runtime governance, dataset ingestion, validation, qualification and publication.

## Local start

```bash
PYTHONPATH=. uvicorn infrastructure.api.main:app --reload
```

## Safety

Source files are untrusted candidates. FastAPI is an adapter, not the authority. PostgreSQL credentials are supplied only through server-side environment variables.
