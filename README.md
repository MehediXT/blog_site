# Universe of Ilm

Universe of Ilm is a bilingual Islamic question-and-answer platform. Registered users submit public or private questions; a moderator assigns a verified scholar and a different reviewer; only an approved revision becomes a released fatwa.

## Features

- Session authentication with CSRF-protected JSON endpoints
- Email verification state before question submission
- Private-by-default questions and restricted clarification history
- Moderator assignment to two different approved scholars
- Immutable answer revisions and independent review decisions
- Public publications that contain only approved, redacted wording
- Bookmarks, in-app notifications, and a durable email outbox
- Bangla and English public shell with locale-prefixed Next.js routes
- Legacy posts and comments retained for migration but no longer writable

## Technology

- Python 3.12+
- Django 6.0+
- Django REST Framework (production dependency)
- Next.js and TypeScript
- PostgreSQL
- Redis and Celery

## Local setup

Clone the repository and enter the project directory:

```bash
git clone <repository-url>
cd blog_site
```

Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate
```

On Windows PowerShell, activate it with:

```powershell
.venv\Scripts\Activate.ps1
```

Install the pinned backend dependencies:

```bash
python -m pip install -r requirements.txt
```

Apply the database migrations:

```bash
python manage.py migrate
```

Optionally create an administrator account:

```bash
python manage.py createsuperuser
```

Start the development server:

```bash
python manage.py runserver
```

Open `http://127.0.0.1:8000/` in a browser. The administration site is available at `http://127.0.0.1:8000/admin/`.

For the planned PostgreSQL, Redis, Django, Celery, Caddy, and Next.js stack, copy `.env.example` to `.env`, set the secrets, and run:

```bash
docker compose up --build
```

## Configuration

Local development uses SQLite and development-safe defaults. The following environment variables can override the settings:

| Variable | Purpose | Local default |
| --- | --- | --- |
| `DJANGO_DEBUG` | Enables Django debug mode | `True` |
| `DJANGO_SECRET_KEY` | Django cryptographic secret | Development-only fallback |
| `DJANGO_ALLOWED_HOSTS` | Comma-separated allowed hosts | `127.0.0.1,localhost` |
| `DB_ENGINE` | Django database backend | SQLite when unset |
| `DB_NAME` | Database name | `blog` |
| `DB_USER` | Database user | `postgres` |
| `DB_PASSWORD` | Database password | Empty |
| `DB_HOST` | Database host | `localhost` |
| `DB_PORT` | Database port | `5432` |

For PostgreSQL, install its Python driver and set the database variables before running migrations:

```bash
python -m pip install "psycopg[binary]>=3.2"
export DB_ENGINE=django.db.backends.postgresql
export DB_NAME=blog
export DB_USER=postgres
export DB_PASSWORD=your-password
export DB_HOST=localhost
export DB_PORT=5432
python manage.py migrate
```

For production, set a strong `DJANGO_SECRET_KEY`, disable debug mode, configure allowed hosts, and serve the application through a production-ready WSGI server.

## Main routes

| Route | Description |
| --- | --- |
| `/` | Published fatwa list, search, and filtering |
| `/post/<id>/` | Published fatwa details, references, and comments |
| `/create_post_view/` | Authenticated fatwa creation |
| `/accounts/register/` | Account registration |
| `/accounts/login/` | Login |
| `/accounts/dashboard/` | User dashboard |
| `/accounts/password-reset/` | Password reset workflow |
| `/admin/` | Django administration |

The versioned API is under `/api/v1/`. Start with `/api/v1/auth/csrf/`, then use `/api/v1/auth/register/`, `/api/v1/me/questions/`, `/api/v1/fatwas/`, `/api/v1/scholar/assignments/`, and `/api/v1/reviews/`. Private records return 404 when the signed-in user is not part of the authorized team.

## Project structure

```text
blog_site/
├── accounts/          # Authentication, profiles, email verification, and scholar profiles
├── fatwas/            # Categories, methodologies, answer revisions, publications, reports
├── questions/         # Private question workflow and clarifications
├── moderation/        # Moderation app boundary for assignment tools
├── notifications/     # In-app notifications and durable email outbox
├── blog/              # Project settings and root URL configuration
├── posts/             # Post, category, and comment models and views
├── static/            # CSS and JavaScript
├── templates/         # Shared, post, dashboard, and auth templates
└── manage.py          # Django command-line entry point
```

## Tests and validation

Run the automated tests:

```bash
python manage.py test
```

Run Django's configuration checks:

```bash
python manage.py check
```

When a model changes, create and apply its migration:

```bash
python manage.py makemigrations
python manage.py migrate
```

The original `posts` app is a migration archive. Its old creation and comment routes return `410 Gone`; new content must use the question/review workflow.
