# I006 FastAPI AWS Deployment and HTTPS Delivery

This package deploys the existing FastAPI application as a release-keyed systemd service behind Caddy. It does not provision AWS resources automatically and does not run database migrations automatically.

## Security boundaries

- Uvicorn listens only on `127.0.0.1:8000`.
- Caddy is the only public HTTP/HTTPS listener.
- PostgreSQL credentials remain in `/etc/nexa/infrastructure-api.env` with mode `0600`.
- GitHub deployment secrets contain only SSH and public health information.
- RDS remains private.

## Release lifecycle

1. Build a commit-keyed archive.
2. Upload it to the server.
3. Extract to `/opt/nexa/infrastructure-api/releases/<sha>`.
4. Compile and install dependencies.
5. Atomically switch the `current` symlink.
6. Restart and qualify health.
7. Restore `previous` automatically if activation health fails.

AWS provisioning, VPC peering, DNS and certificate issuance are Phase F manual operations.
