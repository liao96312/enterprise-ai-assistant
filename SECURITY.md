# Security Notes

## Production defaults

- Set `AUTH_ENABLED=true` in production.
- Use a long random `ADMIN_TOKEN`.
- Restrict `CORS_ORIGINS` to your real domain.
- Keep `.env` outside version control.
- Back up `data/raw` and `data/chroma`.

## API keys

API keys are stored in `.env` when saved through the web UI. The `/settings` endpoint only returns masked keys.

## Network exposure

Run the application behind Nginx or another reverse proxy with HTTPS enabled. The included `deploy/nginx.conf` is a starting point and should be adjusted for your domain and certificate setup.
