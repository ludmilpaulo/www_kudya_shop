# Deploy Kudya Super App API to Production

Target: `https://www.kudya.store` (currently serves legacy routes only; new `/api/*` must be deployed).

## 1. Server prerequisites

- Python 3.10+ (3.12 recommended)
- PostgreSQL (production) or keep SQLite only for staging
- System libs for WeasyPrint (invoices): `pango`, `cairo`, `gdk-pixbuf` (on Ubuntu: `apt install libpango-1.0-0 libgdk-pixbuf2.0-0 libcairo2`)
- Optional: Redis for Channels/WebSockets (`REDIS_URL=redis://127.0.0.1:6379/0`)

## 2. Deploy code

```bash
cd /path/to/www_kudya_shop
git pull origin main   # or upload your release bundle
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## 3. Environment (`.env`)

```env
DJANGO_SECRET_KEY=<strong-secret>
DJANGO_DEBUG=False
DJANGO_ALLOWED_HOSTS=www.kudya.store,kudya.store,127.0.0.1

# If using PostgreSQL:
# DATABASE_URL=postgres://user:pass@host:5432/kudya

# WebSockets (optional)
# REDIS_URL=redis://127.0.0.1:6379/0

CORS_ALLOWED_ORIGINS=https://www.kudya.store,https://kudya.vercel.app
```

Ensure `www_kudya_shop/settings.py` reads these vars (or set them in your host panel).

## 4. Database migrate + seed

```bash
source venv/bin/activate
./scripts/setup_superapp.sh
# Or manually:
python manage.py makemigrations
python manage.py migrate
python manage.py seed_superapp
python manage.py collectstatic --noinput
```

**Important:** `kudya_platform` replaced the old `platform` app name (avoids Python stdlib conflict). Do not rename it back.

## 5. Run application

### HTTP only (simplest)

```bash
gunicorn www_kudya_shop.wsgi:application --bind 0.0.0.0:8000 --workers 3
```

### HTTP + WebSockets (rides live tracking)

1. In `settings.py` `INSTALLED_APPS`, uncomment `daphne` (first), `channels`, `realtime`.
2. Start with Daphne:

```bash
daphne -b 0.0.0.0 -p 8000 www_kudya_shop.asgi:application
```

### PythonAnywhere

1. Upload/pull code into your web app directory.
2. Virtualenv: install `requirements.txt`.
3. **Web** tab → WSGI file points to `www_kudya_shop.wsgi:application`.
4. Run migrations in a **Bash** console (steps 4).
5. Reload web app.
6. For ASGI/WebSockets, use PA’s ASGI support or a separate always-on task with Daphne + Redis.

### Nginx reverse proxy (VPS)

```nginx
server {
    server_name www.kudya.store;
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
    }
    location /static/ { alias /path/to/www_kudya_shop/staticfiles/; }
    location /media/  { alias /path/to/www_kudya_shop/media/; }
}
```

## 6. Verify production

```bash
./venv/bin/python scripts/live_api_test.py
```

Expect **0 failures** on `PRODUCTION` for:

- `GET /api/platform/home-modules/` → 200
- `POST /api/auth/register/` → 201
- `POST /api/rides/estimate/` (with token) → 200

## 7. Frontend apps (no URL change needed)

Apps already point to `https://www.kudya.store`:

| App | Path |
|-----|------|
| kudya-client | `services/types.ts` |
| KudyaParceiro | `services/types.ts` |
| food_deliver | `services/types.ts`, `NEXT_PUBLIC_BASE_API` |

After backend deploy, rebuild mobile (EAS) and redeploy web (Vercel) only if you changed env vars.

## 8. Rollback

Keep a DB backup before migrate. To roll back code: redeploy previous git tag and run `migrate` only if reverse migrations exist.
