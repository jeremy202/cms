# Headless CMS Platform (Strapi-like MVP)

A production-oriented, modular headless CMS built from scratch.

- Backend: Node.js + Express + Prisma + PostgreSQL
- Admin: Vue 3 + Pinia + Vue Router + Tailwind
- Auth: JWT + RBAC
- Media: Multer local upload (cloud-ready abstraction)

---

## 1) System architecture

### High-level architecture

```text
[ Vue Admin (SPA) ]
        |
        | HTTP/JSON + JWT
        v
[ Express API Layer ]
  - Auth & RBAC middleware
  - Content Type Builder API
  - Dynamic Entry API Generator
  - Media Upload API
        |
        v
[ Service Layer ]
  - AuthService
  - ContentTypeService
  - EntryService
  - MediaService
        |
        v
[ Prisma ORM ] ---> [ PostgreSQL ]
```

### Architectural decisions

- **MVP storage strategy**: single `Entry` table with `data JSON`.
- **Why**: fast iteration, schema agility, no runtime migrations per content type.
- **API generation**: generic route controller resolving `:contentType` -> schema -> CRUD behavior.
- **RBAC**:
  - Admin: content-type builder + full CRUD + delete.
  - Editor: content CRUD, media upload.
  - Public: read-only dynamic GET endpoints (if desired; currently unauthenticated reads are enabled for dynamic GET).

---

## 2) Database schema design

Prisma models:

- `User`: email, passwordHash, role (`ADMIN`, `EDITOR`)
- `ContentType`: name, apiId, version, schema(JSON), createdBy
- `ContentTypeField`: normalized field definitions for builder and UI form generation
- `Entry`: contentTypeId + `data` (JSON) + publish state
- `MediaFile`: uploaded file metadata and URL

### MVP dynamic data option tradeoff

#### Option A (implemented): single `entries` table + JSON

**Pros**
- no runtime DDL
- supports schema edits/versioning easily
- simplest API generator
- best MVP speed

**Cons**
- weaker DB-level constraints/indexing per custom field
- complex filtering at scale
- limited relational integrity on dynamic keys

#### Option B (advanced): generate tables per content type

**Pros**
- strong SQL constraints/indexes
- faster field-level querying at scale
- cleaner relational joins

**Cons**
- runtime migrations and deployment complexity
- harder rollbacks/version compatibility
- significantly higher operational risk

Recommendation: ship Option A first, evolve hot content types to Option B later.

---

## 3) Step-by-step implementation plan

1. **Foundation**
   - Setup Express, Prisma, Postgres, env config
   - Add security middleware: Helmet, CORS, rate limit
2. **Auth + RBAC**
   - Register/login endpoints, JWT issue/verify
   - Role middleware (`authorize`)
3. **Content Type Builder**
   - Create/list/update content types
   - Persist schema JSON and normalized fields
   - Version bump on schema edits
4. **Dynamic Entry Engine**
   - Generic CRUD for `/:contentType`
   - Runtime validation against stored schema
   - Pagination/filter/sort
5. **Media**
   - Upload endpoint (Multer)
   - Persist file metadata
6. **Admin SPA**
   - Auth pages
   - Builder UI
   - Dynamic form renderer
   - Content CRUD pages
   - Media upload UI
7. **Hardening**
   - Add audit logs, tests, background jobs
   - add caching, search index, and observability

---

## 4) Folder structure

```text
/backend
  /prisma
    schema.prisma
  /src
    /config
    /controllers
    /middleware
    /routes
    /services
    /utils
    /validators
    app.js
    server.js

/admin
  /src
    /api
    /components
    /layouts
    /pages
    /router
    /stores
```

---

## 5) Key code examples

### A) Dynamic content-type creation

- Endpoint: `POST /api/content-types`
- Validates schema
- Stores JSON + normalized `ContentTypeField[]`

See:
- `backend/src/controllers/contentType.controller.js`
- `backend/src/services/contentType.service.js`

### B) Auto API generator

Generic routes:

- `POST /api/:contentType`
- `GET /api/:contentType`
- `GET /api/:contentType/:id`
- `PUT /api/:contentType/:id`
- `DELETE /api/:contentType/:id`

Handled by:
- `backend/src/routes/dynamic.routes.js`
- `backend/src/controllers/entries.controller.js`
- `backend/src/services/entry.service.js`

### C) Auth system

- `POST /api/auth/register`
- `POST /api/auth/login`
- `GET /api/auth/me`

Files:
- `backend/src/controllers/auth.controller.js`
- `backend/src/services/auth.service.js`
- `backend/src/middleware/auth.middleware.js`

### D) Vue dynamic form rendering

`DynamicEntryForm.vue` renders fields based on schema metadata (type-driven inputs).

File:
- `admin/src/components/DynamicEntryForm.vue`

---

## 6) Best practices for scaling

1. **Schema governance**
   - Add migration plans between content-type versions
   - Lock schema changes in production with approval flow
2. **Query performance**
   - Add JSONB indexes for hot fields
   - Move high-traffic types to generated SQL tables (hybrid model)
3. **Security**
   - refresh tokens + rotation
   - password reset, email verification, 2FA
   - per-route permission matrix (type + action)
4. **Media scalability**
   - move to S3/R2/GCS adapters
   - async image processing + CDN URLs
5. **Observability**
   - structured logs, tracing, metrics, error alerts
6. **Reliability**
   - queue-based async jobs
   - backups + PITR
   - zero-downtime migrations

---

## Run locally

### Backend

```bash
cd backend
cp .env .env.local # optional
npm install
npm run generate
npm run migrate
npm run seed
npm run dev
```

Backend default: `http://localhost:4000`

### Admin

```bash
cd admin
npm install
npm run dev
```

Admin default: `http://localhost:5173`

---

## API quick reference

- Auth
  - `POST /api/auth/register`
  - `POST /api/auth/login`
  - `GET /api/auth/me`
- Builder
  - `GET /api/content-types`
  - `POST /api/content-types` (ADMIN)
  - `PUT /api/content-types/:id` (ADMIN)
- Dynamic entries
  - `POST /api/:contentType`
  - `GET /api/:contentType`
  - `GET /api/:contentType/:id`
  - `PUT /api/:contentType/:id`
  - `DELETE /api/:contentType/:id`
- Media
  - `POST /api/media`
