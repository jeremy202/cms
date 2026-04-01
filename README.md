# Website Management CMS

A multi-user CMS with a Flask backend API and a Vue + Tailwind admin frontend.

## Stack

- Backend: Flask + SQLite
- Frontend: Vue 3 (Vite) + Tailwind CSS
- Tests: Pytest

## Features

- Multi-user auth (register/login/logout) with session cookies
- Website management (name, domain, stack, status, tags)
- Per-website page management (markdown content)
- Per-website deployment tracking (Vercel/Netlify)
- Search/filter/sort across websites
- JSON APIs powering the Vue admin

## Project structure

- `cms/` Flask app and API routes
- `frontend/` Vue + Tailwind single-page app
- `tests/` backend tests

## Run backend

```bash
pip install -r requirements.txt
python app.py
```

Backend runs at `http://127.0.0.1:5000`.

## Run frontend

In another terminal:

```bash
cd frontend
npm install
npm run dev
```

Frontend runs at `http://127.0.0.1:5173` and proxies `/api` + `/auth` to Flask.

## Build frontend

```bash
cd frontend
npm run build
```

## Run tests

```bash
python3 -m pytest
```

## Core API endpoints used by frontend

- `GET /api/me`
- `POST /auth/register`
- `POST /auth/login`
- `POST /auth/logout`
- `GET /api/websites`
- `POST /api/websites`
- `PUT /api/websites/<website_id>`
- `DELETE /api/websites/<website_id>`
- `GET /api/websites/<website_id>/pages`
- `POST /api/websites/<website_id>/pages`
- `PUT /api/pages/<page_id>`
- `DELETE /api/pages/<page_id>`
- `GET /api/websites/<website_id>/deployments`
- `POST /api/websites/<website_id>/deployments`
- `PUT /api/deployments/<deployment_id>`
- `DELETE /api/deployments/<deployment_id>`
