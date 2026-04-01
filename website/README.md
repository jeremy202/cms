# CMS Test Website

This is a lightweight test website that consumes your CMS delivery API.

## Run

```bash
npm install
npm run dev
```

Default URL: `http://localhost:5174`

## What it tests

- Dataset selection (`production`, `staging`, etc.)
- Content type endpoint mode:
  - `/api/delivery/:dataset/:contentType`
- Query mode:
  - `/api/delivery/query?dataset=...&query=*[_type=="post"]{title,slug}`
- Optional delivery token for private datasets

## Typical flow

1. Start backend (`http://localhost:4000`)
2. In admin, create content type (e.g. `post`) and entries
3. Mark entries as published if needed
4. Open this website and click "Refresh from CMS"

The page displays fetched entries and raw JSON for quick debugging.
