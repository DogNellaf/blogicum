# Blogicum

> 🇬🇧 English | [🇷🇺 Русский](README.ru.md)

A social network for personal diary publishing built with Django. Users can register, run a blog, publish posts with images, attach them to categories and locations, comment on others' posts, and edit their profile. Posts support scheduled publishing, unpublishing, and category grouping.

## Features

- Registration, authentication, password change and recovery
- Create, edit, and delete posts (with deletion confirmation)
- Image upload for posts
- Scheduled publishing (future date) and unpublishing
- Post categories and locations; dedicated category pages
- Comments: add, edit, and delete by the author
- Comment counter on each post
- User profile page with a list of their posts
- Pagination (10 posts per page)
- Custom error pages for 403 (CSRF), 404, and 500
- Static "About" and "Rules" pages
- Admin panel for all models

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | Python 3.9+, Django 3.2 |
| Database | SQLite (default) |
| Frontend | django-bootstrap5 |
| Image handling | Pillow |
| Testing | pytest, Django test runner, coverage, flake8 |

## Requirements

- Python 3.9+
- pip

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd <repository-dir>

# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate        # Linux / macOS
source .venv/Scripts/activate    # Windows (Git Bash)

# Install dependencies
pip install -r requirements.txt

# Apply migrations and run the development server
cd blogicum
python manage.py migrate
python manage.py runserver
```

Optionally, create a superuser for the admin panel:

```bash
python manage.py createsuperuser
```

The application will be available at `http://127.0.0.1:8000/`, the admin panel at `http://127.0.0.1:8000/admin/`.

## Environment Variables

Sensitive settings are read from the environment (defaults are provided for local development):

| Variable | Description | Default |
|---|---|---|
| `SECRET_KEY` | Django secret key | insecure dev key |
| `DEBUG` | Enable debug mode (`true`/`false`) | `true` |
| `ALLOWED_HOSTS` | Comma-separated list of allowed hosts | `localhost,127.0.0.1` |

In development mode, emails (e.g. password recovery) are saved as files in the `sent_emails/` directory.

## Running Tests

The project's own test suite covers models, forms, views, and pages at 100%:

```bash
# From the blogicum/ directory
python manage.py test

# With a coverage report
coverage run --source='blog,pages' --omit='*/migrations/*,*/tests/*' \
    manage.py test blog pages
coverage report -m
```

Run the external acceptance suite (pytest) from the repository root:

```bash
pytest
```

Check code style:

```bash
flake8
```

## Project Structure

```
blogicum/                # Django project directory (next to manage.py)
├── blog/                # Core app: posts, comments, profiles
│   ├── models.py        # Category, Location, Post, Comment + PostQuerySet manager
│   ├── views.py         # Blog views
│   ├── forms.py         # Post, comment, profile, and registration forms
│   ├── admin.py         # Admin configuration
│   ├── urls.py
│   └── tests/           # App tests (models, forms, views)
├── pages/               # Static pages and error handlers + tests.py
├── blogicum/            # Project settings (settings, urls, wsgi/asgi)
├── templates/           # HTML templates
├── static/              # Static files (css, images)
└── manage.py

# Repository root:
# requirements.txt, setup.cfg, pytest.ini, tests/ (acceptance tests)
```

## License

[MIT](LICENSE)
