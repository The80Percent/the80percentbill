# The 80 Percent Bill

A Django website for The 80% Bill — 20 bills that 80%+ of Americans support. Sign the pledge, read the bill, and support the project.

Migrated from the Streamlit app at `/Users/bennett/Development/JS/the-80-percent-bill`.

## Architecture

The project lives at `python/the_80_percent_bill/`. All commands run from there.

```
python/the_80_percent_bill/        # Project root (run manage.py from here)
├── manage.py
├── requirements.txt
├── .env                           # Secrets (copy from .env.example)
├── .env.example
├── venv/
├── db.sqlite3
├── templates/                     # Shared base template
│   └── base.html
├── static/
│   └── css/
│       └── theme.css
├── the_80_percent_bill/           # Django project config
│   ├── settings.py
│   ├── urls.py                   # Root URL router (Django built-in)
│   ├── context_processors.py
│   └── ...
├── core/                          # Shared utilities
│   ├── geo.py                    # OSM + Geocodio address → district lookup
│   └── sheets.py                # Pledge storage (Supabase or SQLite)
├── home/                          # Feature: landing page
│   ├── views.py
│   ├── urls.py
│   └── templates/home/
├── bill/                          # Feature: read the 20 articles
│   ├── views.py
│   ├── articles.py               # Bill article data
│   ├── urls.py
│   └── templates/bill/
└── pledge/                        # Feature: sign the pledge (3-step flow)
    ├── views.py
    ├── urls.py
    └── templates/pledge/
```

### URLs (Django routing)

| Path | Feature |
|------|---------|
| `/` | Home — hero + CTAs |
| `/pledge/` | Sign the pledge (district lookup → name/email → success) |
| `/bill/` | Read the 20 bill articles |
| `/admin/` | Django admin |

---

## Setup

> **Important:** Run all commands from the project root: `cd python/the_80_percent_bill`

1. **Virtual environment**

   ```bash
   python -m venv venv
   source venv/bin/activate   # macOS/Linux. Windows: venv\Scripts\activate
   ```

2. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

3. **Configure secrets** — copy `.env.example` to `.env` and fill in:

   ```bash
   cp .env.example .env
   ```

   - `GEOCODIO_API_KEY` — Required for address → congressional district lookup
   - `SUPABASE_DB_PASSWORD` — If set, pledges are stored in Supabase Postgres (production). Otherwise SQLite (`db.sqlite3`).

4. **Migrations**

   ```bash
   python manage.py migrate
   ```

5. **Create admin user** (optional)

   ```bash
   python manage.py createsuperuser
   ```

6. **Run the server**

   ```bash
   python manage.py runserver
   ```

   Open **http://127.0.0.1:8000/** — Home, Pledge, and Bill pages are available.

---

## Quick reference

| Command | Description |
|---------|-------------|
| `python manage.py runserver` | Start dev server |
| `python manage.py migrate` | Apply migrations |
| `python manage.py createsuperuser` | Create admin user |
# the80percentbill
