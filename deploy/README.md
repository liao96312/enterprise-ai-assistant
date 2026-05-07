# Enterprise Deployment

## Docker

```bash
cp .env.example .env
docker compose up -d --build
```

Health checks:

```bash
curl http://127.0.0.1:8000/health
curl http://127.0.0.1:8000/ready
```

## VPS + systemd + Nginx

```bash
cd /opt/enterprise-ai-assistant
python3.11 -m venv .venv
. .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Edit `.env`, then install service:

```bash
sudo cp deploy/enterprise-ai-assistant.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now enterprise-ai-assistant
sudo cp deploy/nginx.conf /etc/nginx/sites-available/enterprise-ai-assistant
sudo ln -s /etc/nginx/sites-available/enterprise-ai-assistant /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

Production checklist:

- Set `AUTH_ENABLED=true`
- Set a long random `ADMIN_TOKEN`
- Set `CORS_ORIGINS=https://your-domain.com`
- Configure HTTPS certificates at Nginx
- Persist `data/` and `.env`
- Back up `data/raw` and `data/chroma`
