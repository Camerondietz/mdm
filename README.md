# MDM — Master Data Management

A unified, standards-aligned data model for connecting data across your businesses
and personal life. Built to run on a laptop for a single user and to scale toward
enterprise use. Django + PostgreSQL, JSON-LD / Schema.org canonical model, a REST
API for other systems, and a clean search UI.

---

## Standards alignment

| Purpose               | This project |
|-----------------------|--------------|
| Canonical data model  | **JSON-LD** (every entity serializes at `/api/<type>/<id>/jsonld/`) |
| Semantic meaning       | **Schema.org** types + a `metadata` JSON field for custom ontology |
| Relationships          | Relational now; generic **`Relationship`** triples are the bridge to a future **graph** model |
| IDs                    | **UUID** primary keys + stable **URIs** (`@id`) |
| Validation             | DRF serializers + model constraints (JSON-Schema-shaped payloads) |
| Storage                | **PostgreSQL** |
| Search                 | **PostgreSQL full-text search** now; pluggable to **OpenSearch** later |
| AI interoperability    | JSON-LD + an `embedding` field on documents (JSON now, **pgvector** later) |

---

## Architecture

Two Django apps:

- **`core`** — shared infrastructure: `BaseModel` (UUID, timestamps, provenance,
  JSON-LD), and the generic **`Identifier`**, **`ContactPoint`**, and
  **`Relationship`** tables that attach to *any* entity.
- **`mdm`** — the domain, organized into subpackages:
  - `models/` — Person, Organization, Department, Employment, Item, Document,
    Location, and the taxonomy tables.
  - `admin/` — fast, autocomplete-driven editing with inline contacts, IDs,
    departments, and employees.
  - `api/` — DRF serializers, viewsets, and router.
  - `search/` — the login-required unified search page and per-entity detail pages.

### Entities

| Entity | Schema.org | Notes |
|--------|-----------|-------|
| Person | `Person` | Personal data only; jobs live on Employment |
| Organization | `Organization` | Self-referential subsidiaries, locations, ownership |
| Department | `Organization` | Nestable, belongs to an Organization |
| Employment | `OrganizationRole` | **Business** link Person ⇄ Organization (title, manager, work email) |
| Item | `Product` | SKU, features, pricing, related items/documents |
| Document | `CreativeWork` | Authors, topics, citations, embeddings, permissions |
| Location | `Place` | Hierarchical country → … → address, coordinates |
| Taxonomies | — | Organization/Employment/Document types, categories, roles, skills, topics |

---

## Prerequisites

- Python 3.11+ (dev uses the local `.venv`, already created with 3.13)
- Docker Desktop (for Postgres in dev, and for the Raspberry Pi deployment)

---

## 🚀 Local development (your next steps)

The Django project and all code are ready. Dependencies are installed in `.venv`.
Pick up from here:

**1. Start PostgreSQL** (via Docker — matches the `.env` credentials):

```bash
docker compose up -d db
```

*(Or use a local Postgres install and set `POSTGRES_HOST`/`POSTGRES_PORT`/`POSTGRES_DB`/`POSTGRES_USER`/`POSTGRES_PASSWORD` in `.env` to match it.)*

**2. Create and apply migrations:**

```bash
.\.venv\Scripts\python.exe manage.py makemigrations
```
```bash
.\.venv\Scripts\python.exe manage.py migrate
```

**3. Create your admin user:**

```bash
.\.venv\Scripts\python.exe manage.py createsuperuser
```

**4. Run the app:**

```bash
.\.venv\Scripts\python.exe manage.py runserver
```

Then open:
- **Search UI** → http://localhost:8000/ (log in with the superuser)
- **Admin** → http://localhost:8000/admin/
- **API root** → http://localhost:8000/api/

> Tip: seed the taxonomy tables first (Organization types, Employment types,
> Document types, Categories, Roles, Skills, Topics) in the admin — they power the
> dropdowns on the main entities.

---

## Web UI

- **`/`** — one search box across **all** entities (People, Organizations,
  Departments, Employment, Items, Documents, Locations). Full-text ranked, with
  type-filter chips (showing counts) and sort (relevance / name / newest / oldest).
- **Detail pages** — every result links to a rich view. An **Organization** page
  shows its details *plus* each department with the employees in it; a **Person**
  page shows contact points, employment history, skills, and family links.
- Login required throughout (`/accounts/login/`).

---

## REST API

Auth: **Token** (for other systems) or **Session** (for the browsable API).
Reads require login; writes require the matching Django model permission
(add/change/delete), which you grant per user/group in the admin.

**Get a token:**

```bash
curl -X POST http://localhost:8000/api/auth/token/ \
  -d "username=<you>&password=<pw>"
# → {"token": "abc123..."}
```

**Use it:**

```bash
curl http://localhost:8000/api/people/ \
  -H "Authorization: Token abc123..."
```

**Endpoints** (all under `/api/`): `people`, `organizations`, `departments`,
`employments`, `items`, `documents`, `locations`, `contact-points`,
`identifiers`, `relationships`, plus the taxonomies (`organization-types`,
`employment-types`, `item-categories`, `document-types`, `roles`, `skills`,
`topics`).

Each supports `GET` (list/retrieve), `POST`, `PUT/PATCH`, `DELETE`, and:
- **Filtering** — e.g. `/api/employments/?organization=<uuid>&is_primary=true`
- **Text search** — `/api/people/?search=smith`
- **Ordering** — `/api/documents/?ordering=-updated_at`
- **Pagination** — `?limit=50&offset=100`
- **JSON-LD** — `/api/organizations/<uuid>/jsonld/`

---

## 🐳 Deploy to Raspberry Pi (Docker)

Use **64-bit Raspberry Pi OS**. Host ports: **Django 8002**, **Postgres 5433**
(chosen to avoid clashing with other containers). The public site is served over
HTTPS at **https://mdm.cameron-dietz.com** via a Cloudflare Tunnel — no router
ports are opened.

1. Copy this project to the Pi.
2. Create the production env file and edit it:
   ```bash
   cp .env.example .env
   ```
   Set at minimum: `DJANGO_SECRET_KEY` (generate a fresh one), `DJANGO_DEBUG=false`,
   `DJANGO_ALLOWED_HOSTS=mdm.cameron-dietz.com,<pi-lan-ip>`, `POSTGRES_PASSWORD`,
   `MDM_BASE_URI=https://mdm.cameron-dietz.com`,
   `DJANGO_CSRF_TRUSTED_ORIGINS=https://mdm.cameron-dietz.com`, and
   `CLOUDFLARE_TUNNEL_TOKEN` (see step 3).
3. **One-time Cloudflare Tunnel setup** (Zero Trust dashboard → Networks → Tunnels):
   - Create a tunnel; copy its **token** into `.env` as `CLOUDFLARE_TUNNEL_TOKEN`.
   - Add a **public hostname**: `mdm.cameron-dietz.com` → service **`http://web:8000`**.
     (Cloudflare creates the DNS record for the domain automatically.)
4. Build and start the full production stack (Postgres + app + tunnel). Migrations
   and `collectstatic` run automatically on startup:
   ```bash
   docker compose --profile production up -d --build
   ```
5. Create your admin user:
   ```bash
   docker compose exec web python manage.py createsuperuser
   ```
6. Open **https://mdm.cameron-dietz.com** (or `http://<pi-ip>:8002/` on the LAN).

Static files are served by WhiteNoise; TLS is terminated at Cloudflare's edge, and
the app trusts the `X-Forwarded-Proto` header — so keep `DJANGO_SECURE_SSL_REDIRECT=false`
to avoid redirect loops. To run the stack **without** the tunnel (e.g. LAN test),
omit the profile: `docker compose up -d --build`.

---

## Future scale-up (already designed for)

- **Search → OpenSearch/Elasticsearch:** the `mdm/search/registry.py` list stays;
  swap the query engine in `mdm/search/views.py`. Add `opensearch-py`.
- **Embeddings → pgvector:** switch `Document.embedding` from `JSONField` to a
  `pgvector` `VectorField`, use the `pgvector/pgvector` Postgres image, and index
  for similarity search. Add `pgvector`.
- **Relational → Graph:** the `Relationship` (subject-predicate-object) table is a
  triple store already; export it to a property graph when the time comes.
- **Party model:** Person and Organization share the MDM "Party" concept; a
  `Party` supertype can be introduced without disturbing the API surface.
