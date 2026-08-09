# NexiLabs development authentication fixtures

Bundle 12D keeps credential verifiers and the complete Enigma lookup catalogues under `development/auth/private/`.

That directory is intentionally ignored by Git and must not be placed under `frontend/public/`, added to the PWA application-shell cache, or forced into a commit.

For local development:

1. Keep the three qualified Enigma CSV files supplied by the Bundle 12D delivery package in `development/auth/private/enigma/`.
2. Generate local hashed credential fixtures with:

   `PYTHONPATH=. python development/auth/generate_local_credentials.py`

3. Run the local authentication authority with:

   `PYTHONPATH=. python -m backend.auth.development_server --host 127.0.0.1 --port 8766`

The default generated accounts are development-only and must never be treated as production credentials.

Future production replacement boundary:

`NexiLabs UI -> authentication client -> production Authentication API -> PostgreSQL`

The browser contract should not need redesign when the development authority is replaced.
