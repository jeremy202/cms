# Website Management CMS

A lightweight CMS to manage all websites you have built, with per-site page management.

## Features

- Website registry (name, domain, stack, status)
- Per-website page management (title, slug, SEO description, published)
- Dashboard with page counts and recent page updates
- JSON API endpoints:
  - `GET /api/websites`
  - `GET /api/websites/<website_id>/pages`
- SQLite storage (zero external database setup)

## Tech Stack

- Python 3.10+
- Flask 3+
- SQLite
- Pytest

## Run locally

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://127.0.0.1:5000`.

## Run tests

```bash
pip install -e .[dev]
pytest
```

## Data model

### websites

- `id`
- `name`
- `domain` (unique)
- `tech_stack`
- `status` (`active`, `maintenance`, `archived`)
- `created_at`

### pages

- `id`
- `website_id` (FK -> websites.id)
- `title`
- `slug` (unique per website)
- `seo_description`
- `published` (boolean)
- `updated_at`

## Next improvements (optional)

- Multi-user auth and roles
- Rich text editor for page content
- Search/filter/sort on dashboard
- Deploy targets per website (e.g. Netlify/Vercel metadata)
- Backups and import/export
