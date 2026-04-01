# Website Management CMS

A lightweight multi-user CMS to manage all websites you have built, including pages, deployments, tags, and markdown content.

## Features

- Multi-user authentication (register, login, logout)
- Website registry scoped per user
  - fields: name, domain, tech stack, status, tags
- Per-website page management
  - title, slug, SEO description, published status
  - markdown content editor + rendered preview page
- Deployment tracking per website
  - providers: Vercel or Netlify
  - production/preview URL, branch, status
- Search / filter / sort on dashboard
  - query by name/domain/stack
  - filter by status or tag
  - sort by recency/name/page count
- JSON API endpoints (authenticated)
  - `GET /api/websites`
  - `GET /api/websites/<website_id>/pages`
  - `GET /api/websites/<website_id>/deployments`

## Tech Stack

- Python 3.10+
- Flask 3+
- SQLite
- Markdown + Bleach (safe rendering)
- Pytest

## Run locally

```bash
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` and create a user account.

## Run tests

```bash
pip install -e .[dev]
python3 -m pytest
```

## Data model

### users

- `id`
- `username` (unique)
- `password_hash`
- `role`
- `created_at`

### websites

- `id`
- `owner_id` (FK -> users.id)
- `name`
- `domain` (unique)
- `tech_stack`
- `status`
- `created_at`

### pages

- `id`
- `website_id` (FK -> websites.id)
- `title`
- `slug` (unique per website)
- `seo_description`
- `content_markdown`
- `published`
- `updated_at`

### deployments

- `id`
- `website_id` (FK -> websites.id)
- `provider` (`vercel`/`netlify`)
- `project_name`
- `production_url`
- `preview_url`
- `branch`
- `status`
- `updated_at`

### tags

- `tags` table for unique tags
- `website_tags` join table for many-to-many website tagging
