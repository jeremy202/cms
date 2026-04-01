# Headless CMS Platform (Sanity-like MVP)

A production-oriented, modular headless CMS inspired by Strapi + Sanity workflows.

- Backend: Node.js + Express + Prisma + PostgreSQL
- Admin: Vue 3 + Pinia + Vue Router + Tailwind
- Auth: JWT + RBAC
- Delivery: dataset-aware content API + API tokens
- Media: Multer upload (local disk)

---

## What makes this work like Sanity

This implementation includes Sanity-style website integration primitives:

1. **Datasets** (`production`, `staging`, etc.)
2. **Delivery tokens** for private dataset reads
3. **Published-only delivery API**
4. **Sanity-like query endpoint** (`/api/delivery/query?...`)
5. **Content-type builder + dynamic entries**

You can now plug your website directly into delivery endpoints and update site content from admin.

---

## Architecture

```text
[ Vue Admin ] ---> [ Authoring API (/api/*) ] ---> [ Prisma ] ---> [ PostgreSQL ]
        |                    |
        |                    +--> content types, entries, datasets, tokens
        |
        +--> upload/media

[ Website Frontend ] ---> [ Delivery API (/api/delivery/*) ]
                          - dataset-aware
                          - published-only
                          - API token support
```

---

## Data model (MVP)

- `User` (ADMIN / EDITOR)
- `Dataset` (name, PUBLIC/PRIVATE)
- `ContentType` (schema JSON, version, dataset-scoped)
- `ContentTypeField` (normalized fields)
- `Entry` (JSON data + published flag)
- `ApiToken` (hashed token + scopes + optional dataset scope)
- `MediaFile` (uploads metadata)

---

## Dynamic APIs

### Authoring APIs

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

- `GET /api/datasets`
- `POST /api/datasets` (ADMIN)
- `GET /api/datasets/tokens` (ADMIN)
- `POST /api/datasets/tokens` (ADMIN)
- `DELETE /api/datasets/tokens/:id` (ADMIN)

- `GET /api/content-types?dataset=production`
- `POST /api/content-types` (ADMIN)
- `PUT /api/content-types/:id` (ADMIN)

- `POST /api/:contentType?dataset=production`
- `GET /api/:contentType?dataset=production`
- `GET /api/:contentType/:id?dataset=production`
- `PUT /api/:contentType/:id?dataset=production`
- `DELETE /api/:contentType/:id?dataset=production`

### Delivery APIs (website-facing)

- `GET /api/delivery/:dataset/:contentType`
- `GET /api/delivery/:dataset/:contentType/:id`
- `GET /api/delivery/query?dataset=production&query=*[_type=="post"]{title,slug}`

Behavior:
- returns **published-only** entries
- PUBLIC dataset: no token required
- PRIVATE dataset: requires `Authorization: Bearer <delivery_token>`

---

## Website integration example

### Fetch list of posts

```js
const res = await fetch('http://localhost:4000/api/delivery/production/post')
const json = await res.json()
console.log(json.data)
```

### Fetch private dataset with token

```js
const res = await fetch('http://localhost:4000/api/delivery/staging/post', {
  headers: {
    Authorization: `Bearer ${process.env.CMS_DELIVERY_TOKEN}`,
  },
})
```

### Sanity-like query endpoint

```js
const query = encodeURIComponent('*[_type=="post"]{title,slug}')
const res = await fetch(`http://localhost:4000/api/delivery/query?dataset=production&query=${query}`)
const { result } = await res.json()
```

---

## Run locally

### Backend

```bash
cd backend
npm install
npm run generate
npm run migrate
npm run seed
npm run dev
```

Backend: `http://localhost:4000`

### Admin

```bash
cd admin
npm install
npm run dev
```

Admin: `http://localhost:5173`

---

## Option A vs B (dynamic storage)

### Option A (implemented)
- one `Entry` table with JSON data
- fastest MVP, schema-flexible
- easier auto API generation

### Option B (future)
- generated SQL table per content type
- better indexing/perf for high-scale types
- higher migration and ops complexity

Recommendation: keep Option A for most types, migrate hot types to Option B gradually.

---

## Scaling best practices

- add JSONB indexes for high-query fields
- add audit logs + revision history per entry
- add preview/draft overlays per environment
- add CDN-backed media storage (S3/R2)
- add granular permissions per content type and action
- add request tracing and error monitoring

---

## Test website (integration demo)

A ready-to-run demo website is included in `website/`.

### Run

```bash
cd website
npm install
npm run dev
```

URL: `http://localhost:5174`

This website can consume:

- `GET /api/delivery/:dataset/:contentType`
- `GET /api/delivery/query?dataset=...&query=*[_type=="post"]{title,slug}`

It includes:
- dataset switcher
- content type mode vs query mode
- optional delivery token input for private datasets
- rendered cards + raw JSON payload preview
