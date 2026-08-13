# Universe of Ilm

Universe of Ilm is a Django web application for publishing and discovering Islamic guidance. Contributors can create fatwas, keep them as drafts or publish them, add supporting references, and discuss published entries through threaded comments.

## Features

- User registration, login, logout, password change, and password reset
- Personal dashboard showing a user's posts and comment count
- Draft and published post states
- Categories, keyword search across post content and references, and category filtering
- Optional supporting references with clickable URLs
- Threaded comments and replies for authenticated users
- Class-based list, detail, create, registration, and dashboard views
- Responsive templates and a custom 404 page
- SQLite for local development and optional PostgreSQL configuration

## Technology

- Python 3.12+
- Django 6.0+
- PostgreSQL
- HTML, CSS, and JavaScript

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

Install Django:

```bash
python -m pip install "Django>=6.0,<6.2"
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

## Project structure

```text
blog_site/
├── accounts/          # Authentication forms, views, URLs, and tests
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
