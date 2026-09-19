# Universe of Ilm

Universe of Ilm is a bilingual Islamic question-and-answer platform. Users submit public or private questions; a moderator assigns a verified scholar and an independent reviewer; only an approved revision becomes a public fatwa.

## Features

- Bangla and English public pages with locale-prefixed Next.js routes
- Public fatwa search and category filtering
- JWT access/refresh-token authentication with refresh-token rotation
- Email verification and private-by-default questions
- Scholar assignment, clarification, answer revision, and independent review workflow
- Redacted public publications that do not expose asker identity
- Bookmarks, reports, in-app notifications, and email delivery through Celery
- Django admin tools for categories, methodologies, scholars, questions, and reviews
- The old server-rendered blog frontend and unused legacy app have been removed

## Architecture

The deployment has four application services and two data services:

- Caddy is the public reverse proxy.
- Next.js serves the Bangla and English public pages.
- Django/Gunicorn serves the API and admin; the custom Django template frontend has been removed.
- Celery processes background jobs through Redis.
- PostgreSQL stores production data.
- Caddy serves collected Django static files from a shared Docker volume.

The default Compose configuration is intended for a single server. It exposes Caddy on ports `80` and `443`; Django and Next.js are only reachable inside the Compose network.

## Content workflow

1. A registered and email-verified user submits a public or private question.
2. A moderator reviews the submission and assigns an eligible scholar and a different reviewer.
3. The scholar writes an answer with references and a methodology label.
4. The reviewer approves the revision, requests changes, or rejects it with feedback.
5. Only an approved revision is released to the asker or published in the public fatwa library.

Private questions and clarification messages are restricted to the asker, assigned team, and authorized moderation staff. Public releases use separate, redacted wording and never expose the asker’s account identity.

## Requirements

For a Docker deployment, install:

- Docker Engine
- Docker Compose v2 (`docker compose`)
- A DNS record pointing your production domain to the server

For non-Docker development, use Python 3.12+, Node.js 22+, and npm.

## Deployment tutorial

For the shortest production path, follow [DEPLOYMENT.md](DEPLOYMENT.md). The
sections below explain the same setup in more detail.

### 1. Get the application

```bash
git clone <repository-url> blog_site
cd blog_site
```

### 2. Create the environment file

```bash
cp .env.example .env
```

Edit `.env`. At minimum, use a unique secret key and database password:

```dotenv
DJANGO_DEBUG=False
DJANGO_SECRET_KEY=paste-a-long-random-value-here
DJANGO_ALLOWED_HOSTS=example.com,www.example.com
DJANGO_CSRF_TRUSTED_ORIGINS=https://example.com,https://www.example.com
DB_NAME=universe_of_ilm
DB_USER=universe
DB_PASSWORD=use-a-long-random-password
DB_HOST=db
DB_PORT=5432
REDIS_URL=redis://redis:6379/0
API_ORIGIN=http://django:8000
NEXT_PUBLIC_API_ORIGIN=http://django:8000
```

`DJANGO_CSRF_TRUSTED_ORIGINS` is only needed for Django admin or other browser-based Django POSTs. API clients authenticate with `Authorization: Bearer <access-token>`.

Do not commit `.env` or reuse the example secret in production.

### 3. Configure the domain in Caddy

The checked-in `Caddyfile` is configured for local HTTP on `:80`. For HTTPS deployment, replace the global block and site address with your domain:

```caddyfile
example.com, www.example.com {
    @backend path /api* /admin* /static* /media*
    @static path /static/*
    handle @static {
        root * /srv/static
        file_server
    }
    handle @backend {
        reverse_proxy django:8000
    }
    handle {
        reverse_proxy frontend:3000
    }
}
```

Remove `auto_https off` when using a real domain. Point both DNS records at the server and make ports `80` and `443` reachable; Caddy will request and renew certificates automatically.

### 4. Build and start the stack

```bash
docker compose up -d --build
docker compose ps
```

The Django container automatically runs migrations and `collectstatic` before starting Gunicorn. The shared `staticfiles_data` volume remains available for Django admin assets.

Check the deployment:

```bash
curl http://localhost/api/v1/health/
docker compose logs -f django caddy frontend
```

Open `http://localhost/` for a local deployment, or `https://example.com/` after configuring the domain. The root route redirects to `/bn`; the English shell is at `/en`.

### 5. Create an administrator

Run this once after the services are healthy:

```bash
docker compose exec django python manage.py createsuperuser
```

Then visit `/admin/` and use the account to manage categories, methodologies, scholars, questions, revisions, and review decisions.

### 6. Update the deployment

```bash
git pull
docker compose up -d --build
docker compose ps
```

Migrations and static collection run again when the Django container starts. Keep PostgreSQL and the Docker volumes between releases.

## Local development without Docker

Create a virtual environment and install the pinned backend dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install -r backend/requirements.txt
```

Apply migrations and optionally create an administrator:

```bash
cd backend
python manage.py migrate
python manage.py createsuperuser
```

Start Django on port `8001`:

```bash
python manage.py runserver 127.0.0.1:8001
```

In a second terminal, install and start Next.js:

```bash
cd frontend
npm ci
API_ORIGIN=http://127.0.0.1:8001 NEXT_PUBLIC_API_ORIGIN=http://127.0.0.1:8001 npm run dev
```

Open only `http://127.0.0.1:3000/`. Next.js proxies `/api/`, `/admin/`, `/static/`, and `/media/` to Django.

## Configuration reference

| Variable | Purpose |
| --- | --- |
| `DJANGO_DEBUG` | Set `False` in production. |
| `DJANGO_SECRET_KEY` | Django signing and cryptographic secret. |
| `DJANGO_JWT_SIGNING_KEY` | Optional signing key dedicated to JWTs; defaults to `DJANGO_SECRET_KEY`. |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated hostnames accepted by Django. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Comma-separated full origins allowed to submit cross-origin Django forms/admin requests. |
| `DB_ENGINE` | Database engine; Compose uses PostgreSQL. |
| `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` | Database connection settings. |
| `REDIS_URL` | Celery broker and result backend. |
| `API_ORIGIN` | Server-side Django origin used by Next.js. |
| `NEXT_PUBLIC_API_ORIGIN` | API origin fallback used by Next.js. |

## Main routes

| Route | Description |
| --- | --- |
| `/` | Redirects to the Bangla public shell. |
| `/bn/` | Bangla public home page. |
| `/en/` | English public home page. |
| `/bn/fatwas` and `/en/fatwas` | Locale-filtered public fatwa library. |
| `/admin/` | Django administration. |
| `/api/v1/health/` | Service health endpoint. |
| `/api/v1/fatwas/` | Public catalog API; pass `language=bn` or `language=en`. |

The full versioned API is under `/api/v1/`:

- Authentication: `auth/register/`, `auth/token/`, `auth/token/refresh/`, `auth/logout/`, `auth/verify-email/<token>/`
- Current user: `me/`, `me/questions/`, `me/bookmarks/`, `me/notifications/`
- Public library: `fatwas/`, `categories/`, `methodologies/`, `scholars/`
- Scholar work: `scholar/assignments/`, `scholar/questions/<id>/answer/`
- Moderation and review: `moderation/questions/<id>/assign/`, `reviews/`

Private API resources return `404` when the signed-in user is not authorized to access them.

## Project structure

```text
blog_site/
├── backend/
│   ├── accounts/       # Users, profiles, email verification, scholar profiles
│   ├── fatwas/         # Categories, methodologies, revisions, publications, reports
│   ├── questions/      # Questions and restricted clarification messages
│   ├── notifications/  # In-app notifications and durable email outbox
│   ├── api/            # DRF serializers, generic views, and versioned routes
│   ├── blog/           # Django settings, URLs, WSGI, and Celery setup
│   └── manage.py       # Django command-line entry point
├── frontend/
│   ├── app/            # Locale-aware Next.js routes
│   ├── components/     # Shared public-site components
│   └── lib/            # API client and frontend helpers
├── docker-compose.yml  # PostgreSQL, Redis, Django, Celery, Next.js, and Caddy
├── Caddyfile           # Reverse proxy and static-file routing
└── .env.example        # Local configuration template
```

## Tests and maintenance

Run backend checks and tests:

```bash
cd backend
python manage.py check
python manage.py test
```

Run the frontend type check and production build:

```bash
cd frontend
npm run build
```

When a model changes, create and apply its migration:

```bash
cd backend
python manage.py makemigrations
python manage.py migrate
```

New content uses the question, answer, and review workflow. The old server-rendered blog routes and legacy `posts` app are no longer part of the active project.

## Production checklist

- Set `DJANGO_DEBUG=False` and strong `DJANGO_SECRET_KEY` and `DB_PASSWORD` values.
- Set `DJANGO_ALLOWED_HOSTS` and `DJANGO_CSRF_TRUSTED_ORIGINS` to the real domain.
- Configure DNS and remove `auto_https off` from `Caddyfile`.
- Keep PostgreSQL, Redis, Caddy, and static files on persistent Docker volumes.
- Back up PostgreSQL before upgrades or migration changes.
- Review `docker compose logs` after every deployment and verify `/api/v1/health/`.
