# Universe of Ilm deployment guide

This guide deploys the complete stack with Docker Compose:

- Caddy: public HTTP/HTTPS reverse proxy
- Next.js: bilingual frontend
- Django/Gunicorn: API and admin
- PostgreSQL: application database
- Redis, Celery worker, and Celery Beat: queued notification delivery

The browser uses the public same-origin `/api/v1/` path. Next.js server-rendered
pages call Django over the internal `http://django:8000` service URL.

Before a public launch, provide privileged-account MFA through your access
provider. The application currently authenticates moderators and Django admin
users with passwords and does not include its own MFA enrollment flow. Also
configure off-server backups and restore monitoring; Compose does not supply a
backup destination or monitoring service.

## 1. Prepare the server

Install Docker Engine and Docker Compose v2. Point DNS `A`/`AAAA` records for
your domain to the server. Allow inbound TCP ports `80` and `443`.

```bash
git clone <repository-url> blog_site
cd blog_site
cp .env.example .env
```

## 2. Configure production secrets

Generate two long random values:

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Edit `.env` with values like these. Replace every example value.

```dotenv
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=<first-random-value>
DJANGO_JWT_SIGNING_KEY=<second-random-value>
DJANGO_ALLOWED_HOSTS=example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com
DJANGO_SECURE_SSL_REDIRECT=True
DJANGO_SECURE_HSTS_SECONDS=31536000
SITE_ADDRESS=example.com
PUBLIC_ORIGIN=https://example.com

DB_ENGINE=django.db.backends.postgresql
DB_NAME=universe_of_ilm
DB_USER=universe
DB_PASSWORD=<strong-database-password>
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
CACHE_URL=redis://redis:6379/1
API_ORIGIN=http://django:8000
NEXT_PUBLIC_API_ORIGIN=http://django:8000
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_HOST_USER=your-smtp-user
EMAIL_HOST_PASSWORD=<smtp-password>
EMAIL_USE_TLS=True
DEFAULT_FROM_EMAIL="Universe of Ilm <noreply@example.com>"
CONTACT_EMAIL=support@example.com
```

Replace the SMTP host, credentials, sender, and contact mailbox with working values for your
provider. Registration needs email delivery so users can verify their address.
Never commit `.env` or reuse the sample secret. Django adds the internal
`django` hostname automatically when `DB_HOST=db`.

## 3. Configure Caddy

Set `SITE_ADDRESS` in `.env` to the public domain. The checked-in `Caddyfile`
uses that value; Caddy obtains and renews HTTPS certificates automatically.
To serve `www` too, set `SITE_ADDRESS="example.com, www.example.com"`, add
both DNS records, and include both hosts in Django's allowlist and CSRF origins.
For local HTTP only, keep `SITE_ADDRESS=:80` and
`DJANGO_SECURE_SSL_REDIRECT=False`.

## 4. Build, start, and verify

```bash
docker compose config
docker compose up -d --build
docker compose ps
docker compose exec django python manage.py check --deploy
curl -f https://example.com/api/v1/health/
curl -I https://example.com/bn/
curl -I https://example.com/en/
```

The Django container runs migrations and collects static files before Gunicorn
starts. If a service is unhealthy, inspect the logs:

```bash
docker compose logs --tail=200 django frontend celery celery_beat caddy
```

Expected health response:

```json
{"status":"ok","service":"backend"}
```

## 5. Create the administrator

```bash
docker compose exec django python manage.py createsuperuser
```

Then open `https://example.com/admin/` and create categories, methodologies,
and approved scholar profiles for the review workflow.

Register a test account with an inbox you control and confirm that the
verification email arrives before opening registration to others. Run a
private question through assignment, answer, and independent review; confirm
the answer appears only in that asker's account.

## 6. Verify frontend/API connection

Open these URLs:

- `https://example.com/` — redirects to Bangla
- `https://example.com/bn/` — Bangla frontend
- `https://example.com/en/` — English frontend
- `https://example.com/bn/fatwas` — public fatwa library
- `https://example.com/api/v1/fatwas/?language=bn` — public API

Server-rendered pages call Django through `API_ORIGIN`. Browser requests use
same-origin `/api/v1/` and are routed by Caddy, so no public CORS setup is
required.

## 7. Future deployments

```bash
git pull
docker compose up -d --build
docker compose ps
curl -f https://example.com/api/v1/health/
```

Do not remove the `postgres_data`, `redis_data`, `staticfiles_data`,
`caddy_data`, or `caddy_config` volumes during a normal deployment.

## 8. Backups

Back up PostgreSQL before upgrades or migration changes:

```bash
docker compose exec -T db sh -c 'pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB"' > backup-$(date +%F).sql
```

Automate a daily encrypted off-server backup with your backup provider and
retain 30 days. Test restoring a backup into staging before launch and after
changing the backup process. The command above is a manual snapshot, not a
scheduled backup.

## Local development

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
cd backend
export DB_NAME=blog_site DB_USER=postgres DB_PASSWORD=your-local-password
export DB_HOST=127.0.0.1 DB_PORT=5432
python manage.py migrate
python manage.py runserver 127.0.0.1:8001
```

In another terminal:

```bash
cd frontend
npm ci
API_ORIGIN=http://127.0.0.1:8001 \
NEXT_PUBLIC_API_ORIGIN=http://127.0.0.1:8001 \
npm run dev
```

Open `http://127.0.0.1:3000`.
