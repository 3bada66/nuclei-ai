# Comprehensive Technical Summary: yigit353 Web Programming Course Projects

> Generated: 2026-05-06 | Source: https://github.com/yigit353

---

## Overview

The repository belongs to **Yigit Bekir Kaya**, an Assistant Professor of AI at Istinye University, Istanbul. The 12 web programming course projects (SWE314) form a single progressive application called **ByteBooks** — a bookstore management system built incrementally from a static HTML page to a fully deployed, security-hardened full-stack application.

**Confirmed repos**: week1, week2, week3, week4, week6, week9, week10, week11, week12 (9 repositories — weeks 5, 7, 8 are absent from GitHub).

---

## Week 1 — HTML/CSS Foundations (ByteBooks v1 + v2)

### Project Purpose
Introduce HTML5, CSS, and vanilla JavaScript through a static bookstore UI with no backend. Two progressively enhanced versions exist.

### Main Features
- **v1**: Semantic HTML5 structure, CSS flexbox, dark/light theme toggle with class mutation on `<body>`
- **v2**: DOM manipulation — dynamically adding/removing book cards, a form with `preventDefault()`, event delegation on the grid container, and a live book count counter
- No database, no server, no build tool

### Technologies Used
- Pure HTML5 + CSS3 + vanilla JavaScript (ES6)
- No frameworks, no npm, no bundler

### Project Structure
```
week1-web-programming/
  v1/index.html + styles.css
  v2/index.html + styles.css
  prompts/
```

### Important Code Concepts
- `createBookCard()` function assembles DOM nodes programmatically
- Event delegation: one click listener on the grid handles all remove buttons
- Theme toggle: `document.body.classList.toggle('dark-mode')`
- Form validation with `e.preventDefault()` before reading field values

### What We Can Learn
- How DOM manipulation works before any framework
- CSS animations and transitions
- Responsive layout with flexbox

### Weaknesses or Limitations
- No persistence — page refresh loses all added books
- No backend
- State is implicit in the DOM, not in a JS data structure

---

## Week 2 — FastAPI REST API + SQLite (ByteBooks API)

### Project Purpose
Build a full RESTful API backend with a database, replacing the static frontend with server-managed data.

### Main Features
- Complete CRUD for Books and Authors
- One-to-many relationship: Author has many Books
- Query parameters: genre filter, title search, sorting, pagination
- Auto-seeding: 4 authors and 6 books on startup
- Interactive Swagger docs at `/docs`

### Technologies Used
- Python, FastAPI, SQLModel (SQLAlchemy + Pydantic), SQLite, Uvicorn

### Project Structure
```
bytebooks-api/
  main.py       — routes + app setup + seeding
  models.py     — Author + Book SQLModel tables
  database.py   — session creation
  requirements.txt
```

### Important Code Concepts
- **SQLModel dual-use**: one class serves as both ORM table and Pydantic validation schema
- `Author` model has `books: list[Book] = Relationship(back_populates="author")`
- `Book` model has `isbn: str = Field(unique=True)`, `price: float = Field(ge=0)`
- Lifespan context manager (`@asynccontextmanager`) for startup tasks
- Proper HTTP codes: 201 Created, 204 No Content, 404 Not Found, 409 Conflict
- Author delete blocked if books still exist (referential integrity in application logic)

### What We Can Learn
- How to structure a FastAPI app from scratch
- SQLModel's value proposition (single model definition for DB + validation)
- Auto-generated OpenAPI docs

### Weaknesses or Limitations
- No service layer — all logic in route handlers directly
- Models and schemas are combined (no separation between ORM and Response schemas)
- SQLite only
- No authentication
- No frontend

---

## Week 3 — Service Layer, Validation, and External API Integration

### Project Purpose
Refactor Week 2 into proper layered architecture and add external API integration.

### Main Features
- **v1**: Service layer (`BookService`, `AuthorService`), separated Pydantic schemas (`BookCreate`, `BookUpdate`, `BookResponse`), field-level validation
- **v2**: Async HTTP calls to Open Library API using `httpx.AsyncClient`, ISBN lookup and search, full error mapping (504/503/502/404)

### Technologies Used
- Python, FastAPI, SQLModel, SQLite, httpx (async HTTP), Uvicorn

### Project Structure
```
v1/bytebooks-api/
  main.py, models.py, schemas.py, services.py, database.py
v2/bytebooks-api/
  + external_api.py (OpenLibraryService)
```

### Important Code Concepts
- **Service layer pattern**: `BookService.create_book(session, data)` — routes only call services
- **Schema separation**: `BookCreate` (input), `BookUpdate` (partial), `BookResponse` (output)
- `httpx.AsyncClient` with `timeout=5.0`, maps `TimeoutException` → 504, `ConnectError` → 503
- Proper 409 Conflict for duplicate ISBN

### What We Can Learn
- Why separating schemas from models is essential
- Async external HTTP calls
- How to layer a backend: routes → services → models/database

### Weaknesses or Limitations
- Still SQLite, still no auth
- No tests (only `test_scenarios.md` documentation)

---

## Week 4 — React Frontend (v1 Basic + v2 Interactive)

### Project Purpose
Add a React frontend to the existing API, teaching component composition, hooks, and API integration.

### Main Features
- **v1**: Simple `BookList` component, `useState`/`useEffect` pattern, fetch from FastAPI
- **v2**: Search and filtering, modals for book detail, interactive CRUD forms, Open Library import

### Technologies Used
- React 18, Vite, JavaScript (no TypeScript yet), FastAPI backend from v3

### Project Structure
```
bytebooks-api/          — reused v3 backend
v1/bytebooks-frontend/
  src/App.jsx + src/components/BookList.jsx
v2/bytebooks-frontend/
  src/components/      — more components with modal + forms
```

### Important Code Concepts
- `useEffect` fetching on mount
- State-based navigation (no React Router) — `activePage` string switches rendered component
- CORS configured in FastAPI: `allow_origins=["http://localhost:5173", "http://localhost:5174"]`

### What We Can Learn
- React component lifecycle basics
- Controlled form inputs in React
- Why a Vite proxy or CORS config is needed for dev

### Weaknesses or Limitations
- No React Router — state-based routing does not support browser back/forward
- No TypeScript
- No auth, no testing
- **"Phantom Genre Field" bug**: a field visible in UI was never wired to the API call body

---

## Week 6 — React Dashboard (v1 CRUD + v2 Multi-Page Dashboard)

### Project Purpose
Build a professional admin dashboard with fixed layout, multi-page navigation, and data visualization.

### Main Features
- **v1**: Full CRUD (create/edit/delete), controlled forms
- **v2**: `DashboardLayout` with fixed sidebar and header, 3-page state router (Dashboard/Books/Authors), KPI stat cards, parallel data fetching, data table

### Technologies Used
- React 18, Vite, CSS Grid/Flexbox, JavaScript, FastAPI backend (reused from week4)

### Project Structure
```
v2/bytebooks-frontend/src/
  App.jsx               — activePage state router
  components/DashboardLayout.jsx
  pages/Dashboard.jsx, BooksPage.jsx, AuthorsPage.jsx
```

### Important Code Concepts
- `DashboardLayout` receives `activePage` + `setActivePage` as props from `App`
- Dashboard calculates KPIs: total books, total authors, average price
- `Promise.all([fetchBooks(), fetchAuthors()])` on dashboard mount
- Fixed sidebar with CSS `position: fixed` and main content with `margin-left`

### What We Can Learn
- Professional dashboard layout patterns
- Derived state vs. stored state (KPIs computed from raw data)

### Weaknesses or Limitations
- Still no React Router
- No auth, no testing
- Still SQLite backend

---

## Week 9 — Playwright E2E Testing (v1 Read-Only + v2 Full CRUD Tests)

### Project Purpose
Add comprehensive end-to-end testing using Playwright to cover the full application.

### Main Features
- **v1 tests** (4 files): navigation, book list display, search/filter, book interactions
- **v2 tests** (10 files): delete with dialog, edit with form pre-population, form validation, author page, visual regression with screenshots
- `/reset-db` endpoint added to FastAPI for test state management
- Visual regression: pixel-level screenshot comparison with `threshold: 0.2`, `maxDiffPixels: 100`

### Technologies Used
- Playwright 1.59.1, TypeScript (test files), React 19.2, Vite 7.3.1, FastAPI, Python

### Project Structure
```
bytebooks-api/           — FastAPI + /reset-db endpoint
bytebooks-frontend/
  v1/tests/              — 4 spec files + README
  v2/tests/              — 10 spec files + snapshots/
  package.json           — playwright in devDependencies
```

### Important Code Concepts
- `test.beforeAll(() => page.request.post('/reset-db'))` — ensures clean DB state
- `page.on('dialog', d => d.accept())` — intercepts `window.confirm()` for delete tests
- `page.waitForResponse('**/books')` — waits for API refetch after mutation
- `expect(locator).toHaveScreenshot()` for visual regression
- Search tests verify: filter reduces count, clear restores count, no-results shows `.no-results`

### What We Can Learn
- Full Playwright test architecture for React+FastAPI apps
- How `/reset-db` makes tests deterministic and repeatable
- Visual regression testing approach

### Weaknesses or Limitations
- No auth testing (auth doesn't exist yet)
- Tests run against localhost only — no CI pipeline
- 90%+ coverage not explicitly proven with a coverage report

---

## Week 10 — JWT Authentication (v1 Backend Auth + v2 Frontend Auth)

### Project Purpose
Add a complete authentication system: user registration, login, JWT tokens, and protected routes.

### Main Features
- **v1 (backend)**: `User` model with bcrypt-hashed passwords, `POST /auth/register`, `POST /auth/login` returning JWT, `GET /auth/me` protected, `Depends(get_current_user)` guards write endpoints
- **v2 (frontend)**: `AuthContext` with token in `localStorage`, `ProtectedRoute` component, React Router v6 with public/protected routes, `LoginPage` + `RegisterPage`

### Technologies Used
- FastAPI, SQLModel, passlib[bcrypt], python-jose[cryptography], SQLite, React 19, React Router v6, Vite

### Project Structure
```
v1/bytebooks-api/
  auth_utils.py         — hash_password, verify_password, create_access_token, decode_access_token
  config.py             — SECRET_KEY, ALGORITHM, ACCESS_TOKEN_EXPIRE_MINUTES
  dependencies.py       — get_current_user (HTTPBearer + JWT decode + DB lookup)
  models.py             — User model added
  schemas.py            — UserCreate, UserLogin, TokenResponse
  services.py           — UserService
v2/bytebooks-frontend/src/
  contexts/AuthContext.jsx
  components/ProtectedRoute.jsx
  pages/LoginPage.jsx, RegisterPage.jsx
  App.jsx               — React Router v6 with layout routes
```

### Important Code Concepts
- `get_current_user` returns same 401 regardless of failure reason (security: don't reveal why)
- `WWW-Authenticate: Bearer` header per RFC 6750
- Token `sub` claim holds user ID (stringified)
- `ProtectedRoute` wraps `/books/new` — only authenticated users can add books
- `DashboardLayout` with `<Outlet />` wraps authenticated pages

### What We Can Learn
- Production-quality JWT implementation pattern
- bcrypt salt handling
- Auth state propagation via React Context
- ProtectedRoute pattern with React Router v6

### Weaknesses or Limitations
- Only one auth method (no social login, no 2FA)
- Token stored in `localStorage` (XSS vulnerable)
- No authorization roles
- No token refresh mechanism

---

## Week 11 — Full-Stack Deployment (Vercel + Railway + PostgreSQL)

### Project Purpose
Deploy the full application to production: React frontend on Vercel, FastAPI on Railway with PostgreSQL.

### Main Features
- PostgreSQL via Railway (auto-injected `DATABASE_URL`)
- Dynamic DB URL detection: rewrites `postgres://` → `postgresql://` for SQLAlchemy compatibility
- Environment-specific engine config
- `Procfile` with `web: uvicorn main:app --host 0.0.0.0 --port $PORT`
- `GUIDE.md` with verified deployment workflow

### Technologies Used
- FastAPI, SQLModel, psycopg2-binary, PostgreSQL, uvicorn, React 19, Vite, Vercel CLI, Railway

### Project Structure
```
bytebooks-api/
  database.py           — dual SQLite/PostgreSQL support
  Procfile              — Railway process definition
  .env.example          — env var template
  requirements.txt      — includes psycopg2-binary
bytebooks-frontend/
  (vercel.json added in week12)
GUIDE.md               — deployment walkthrough with gotchas
```

### Important Code Concepts
- `DATABASE_URL.startswith("postgres://")` → replace to `postgresql://`
- SQLite: `connect_args={"check_same_thread": False}`, `echo=True`
- PostgreSQL: no `connect_args`, `echo=False`
- CORS must match production frontend URL exactly (no trailing slash)
- `import.meta.env.VITE_*` baked at build time — env var change requires full redeploy

### What We Can Learn
- How to make one codebase work with both SQLite (dev) and PostgreSQL (prod)
- Railway and Vercel deployment specifics
- Procfile format and port binding

### Weaknesses or Limitations
- No security headers yet (added in week12)
- No rate limiting
- No admin dashboard or role-based access
- Auth is basic JWT only

---

## Week 12 — Security Hardening (CSP, Rate Limiting, WAF, Edge Middleware)

### Project Purpose
Harden the deployed application with frontend and backend security layers.

### Main Features
- **Frontend**: 6 security headers in `vercel.json` (CSP, HSTS with 2-year max-age + preload, `X-Frame-Options: DENY`, `X-Content-Type-Options: nosniff`, Referrer-Policy, Permissions-Policy), edge middleware with `x-request-id`, admin route gating, Vercel WAF rate limiting
- **Backend**: `slowapi` rate limiting (5/minute on login, 30/minute on search), smart rate-limit key (JWT `sub` for authenticated, IP for anonymous), dependency audit, DB private networking on Railway, CORS hardening

### Technologies Used
- FastAPI, slowapi, React 19, Vite, Vercel (edge middleware + WAF), Railway (PostgreSQL private network)

### Project Structure
```
bytebooks-api/
  requirements.txt      — adds slowapi>=0.1.9
  main.py               — @limiter.limit decorators on endpoints
bytebooks-frontend/
  vercel.json           — 6 security headers + SPA rewrites
  src/middleware.ts     — edge middleware (x-request-id, admin gating)
SECURITY.md            — vulnerability reporting policy
GUIDE.md               — security hardening verification steps
```

### Important Code Concepts
- CSP `connect-src` explicitly allows only the Railway backend URL
- `slowapi` limiter uses `get_remote_address` for anonymous, JWT sub for authenticated
- Middleware returns 401 for `/admin/*` before React app loads
- `Permissions-Policy: camera=(), microphone=(), geolocation=()`
- HSTS: `max-age=63072000; includeSubDomains; preload`

### What We Can Learn
- Defense in depth: multiple layers (edge, app, DB)
- How to implement CSP without breaking the app
- Rate limiting strategy: per-user vs per-IP
- Security headers configuration for Vercel

### Weaknesses or Limitations
- Still only basic JWT — no social login, no 2FA, no admin dashboard
- No role-based authorization
- Tests do not cover security headers
- No automated security scanning in CI

---

## Overall Comparison

### Technologies Repeated Across Projects

| Technology | Weeks Used |
|---|---|
| FastAPI | 2, 3, 4, 6, 9, 10, 11, 12 |
| SQLModel | 2, 3, 4, 6, 9, 10, 11, 12 |
| SQLite (dev) | 2, 3, 4, 6, 9, 10 |
| PostgreSQL (prod) | 11, 12 |
| React + Vite | 4, 6, 9, 10, 11, 12 |
| Pydantic validation | 3, 4, 6, 9, 10, 11, 12 |
| Playwright | 9, 12 |
| bcrypt + JWT | 10, 11, 12 |
| httpx (async) | 3–12 |

### Concepts Covered Across the Weeks

- **Week 1**: HTML semantics, CSS flexbox, DOM manipulation, events
- **Week 2**: REST API design, ORM, relational data modeling, HTTP status codes
- **Week 3**: Architecture layering (routes/services/models), schema separation, async external HTTP
- **Week 4**: React fundamentals, component composition, controlled forms, CORS
- **Week 6**: Dashboard layout, derived state, multi-page SPA patterns
- **Week 9**: E2E testing (Playwright), test isolation with `/reset-db`, visual regression
- **Week 10**: Auth (JWT, bcrypt), React context, protected routes
- **Week 11**: Production deployment, PostgreSQL, environment management
- **Week 12**: Security hardening (CSP, HSTS, rate limiting, edge middleware, WAF)

### Progression From Week 1 to Week 12

Linear and deliberate: Static HTML → REST API → Service layer → React frontend → Dashboard → Tests → Auth → Deployment → Security.

Backend grows from `main.py` only (week 2) to 8 files including `auth_utils.py`, `config.py`, `dependencies.py`, `schemas.py`, `services.py` (week 12). Frontend grows from `BookList` only to full React Router v6 app with `AuthContext`, `ProtectedRoute`, and edge middleware.

### Best Projects to Use as References

1. **Week 12** — Most complete; reference for security headers, rate limiting, deployment config
2. **Week 10** — Best reference for auth implementation (clean, well-documented JWT + bcrypt)
3. **Week 9** — Best reference for Playwright test architecture and `/reset-db` pattern
4. **Week 11** — Best reference for deployment workflow, PostgreSQL switching, `Procfile`
5. **Week 3** — Best reference for service layer + schema separation + httpx pattern

### Features Worth Reusing

- `auth_utils.py` with `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`
- `dependencies.py` with `get_current_user` dependency injection
- `config.py` pattern for environment-based secrets
- `database.py` with dual SQLite/PostgreSQL support
- `/reset-db` endpoint (gated to test environments only)
- `vercel.json` with 6 security headers from week 12
- `DashboardLayout` with `<Outlet />` pattern
- `Procfile` format for Railway
- `slowapi` rate limiting with per-user JWT key

### Features We Should Avoid

- State-based routing without React Router (weeks 4, 6, 9) — breaks browser history
- Storing tokens in `localStorage` without XSS mitigation
- Combining ORM models and API schemas in one class (week 2) — over-exposes internals
- Putting all logic in `main.py` without a service layer (week 2)
- Hardcoded fallback `SECRET_KEY` in config
- The "Phantom Genre Field" pattern — always verify fields are wired end-to-end

---

## How These Projects Can Help Us Build Our Own Project

### Which Projects Are Most Relevant

- **Week 10** — cleanest auth implementation (JWT + bcrypt) matching the "Basic Authentication" requirement
- **Week 12** — deployment security (CSP, HSTS, rate limiting) matching the "securing servers" requirement
- **Week 9** — template for Playwright testing for the 90%+ coverage requirement
- **Week 11** — deployment architecture blueprint

### Architecture and Structure to Follow

Follow the week 12 layered architecture:
- `models.py` — SQLModel ORM tables only
- `schemas.py` — Pydantic models for request/response separately
- `services.py` — all business logic (no DB calls in routes)
- `auth_utils.py` — crypto functions isolated
- `dependencies.py` — FastAPI `Depends()` functions
- `config.py` — env var loading
- `database.py` — dual SQLite/PostgreSQL URL handling
- `main.py` — thin routes only, delegates to services

For frontend: React Router v6 layout route pattern from week 11 with `AuthContext` from week 10.

### What Mistakes to Avoid

1. **No social login in any project** — zero examples of Google/GitHub OAuth. Must be built using `authlib` or similar.
2. **No 2FA in any project** — TOTP, SMS, or email 2FA entirely absent. Required for full points.
3. **No admin dashboard** — week 12 gates `/admin/*` in middleware but no actual admin UI or role-based permission management.
4. **No CI/CD pipeline** — Playwright tests exist but no GitHub Actions for auto-running on deploy.
5. **localStorage for tokens** — susceptible to XSS; consider `httpOnly` cookies.
6. **No refresh tokens** — 60-minute access token with no refresh = frequent logouts.

### What Would Make Our Project Stronger

1. **Social login (Google/GitHub OAuth)**: Use `authlib` or `fastapi-users` with OAuth2 — earns bonus points (+5 per provider).
2. **2FA**: Add TOTP (Google Authenticator) using `pyotp`. Store the TOTP secret encrypted per user — earns full auth points + bonus.
3. **Role-based authorization**: Add a `role` field (`admin`, `editor`, `viewer`) to the User model. Admin dashboard for promoting/demoting users — earns the +10 authorization bonus.
4. **CI/CD with Playwright**: GitHub Actions workflow that runs `playwright test` on every push — automates the "90% coverage with each deployment" requirement.
5. **httpOnly cookie storage**: Move JWT from localStorage to httpOnly cookie to close the XSS attack vector.
6. **Refresh token mechanism**: Short-lived access tokens (15 min) + long-lived refresh tokens (7 days) in httpOnly cookies.
7. **Alternative deployment**: Use Fly.io, Render, or a VPS (DigitalOcean, Hetzner) with Docker to earn the +10 "alternatives to Vercel/Railway" bonus.
8. **TypeScript throughout**: Week 9's test files use TypeScript but React source is `.jsx`. Full TypeScript improves correctness.
9. **Build on week12 as base**: Directly extend the week12 structure (auth + security layers already in place) to earn the "using old project as base" full points criterion.

---

# Deep Technical Analysis: week12-web-programming (Full File-by-File Breakdown)
> Source: https://github.com/yigit353/week12-web-programming
> Generated: 2026-05-06

---

## Repository Structure

```
week12-web-programming/
├── .gitignore
├── README.md
├── GUIDE.md                                — Session 1 companion guide (gotchas, verification commands)
├── SECURITY.md                             — Public vulnerability disclosure policy
├── prompts/
│   ├── session1-prompt.md                  — Frontend/edge security curriculum
│   └── session2-prompt.md                  — Backend/origin security curriculum
│
├── bytebooks-api/                          — FastAPI backend
│   ├── .env.example
│   ├── Procfile
│   ├── STARTUP.md
│   ├── auth_utils.py
│   ├── config.py
│   ├── database.py
│   ├── dependencies.py
│   ├── external_api.py
│   ├── main.py
│   ├── models.py
│   ├── requirements.txt
│   ├── schemas.py
│   ├── services.py
│   ├── test_genre.py                       — pytest unit tests (3 tests)
│   └── test_scenarios.md                   — 16 manual edge-case scenarios
│
└── bytebooks-frontend/                     — Vite + React 19 frontend
    ├── .env.development                    — VITE_API_URL=http://localhost:8000
    ├── .env.production.example
    ├── eslint.config.js
    ├── index.html
    ├── middleware.js                       — Vercel Edge middleware
    ├── package.json
    ├── vercel.json                         — SPA rewrite + 6 security headers
    ├── vite.config.js
    ├── src/
    │   ├── App.jsx                         — Route table
    │   ├── main.jsx                        — React root entry point
    │   ├── components/
    │   │   ├── AddBookForm.jsx / .css
    │   │   ├── BookCard.jsx / .css
    │   │   ├── BookDetail.jsx / .css
    │   │   ├── BookList.jsx / .css
    │   │   ├── DashboardLayout.jsx
    │   │   ├── EditBookForm.jsx / .css
    │   │   └── ProtectedRoute.jsx
    │   ├── contexts/
    │   │   └── AuthContext.jsx
    │   ├── pages/
    │   │   ├── AddBookPage.jsx
    │   │   ├── AuthorsPage.jsx
    │   │   ├── BooksPage.jsx
    │   │   ├── Dashboard.jsx
    │   │   ├── LoginPage.jsx
    │   │   └── RegisterPage.jsx
    │   ├── styles/dashboard.css
    │   └── utils/api.js
    ├── v1/tests/                           — 4 Playwright specs
    └── v2/
        ├── global-setup.ts                 — calls /reset-db before each run
        ├── playwright.config.ts
        └── tests/                          — 9 Playwright specs
```

**No `.github/workflows/` directory — zero GitHub Actions CI/CD pipelines.**

---

## Backend — File by File

### `main.py`

**Routes:**

| Method | Path | Auth | Rate Limit |
|--------|------|------|-----------|
| GET | `/books` | No | — |
| POST | `/books` | Yes | — |
| GET | `/books/{id}` | No | — |
| PUT | `/books/{id}` | Yes | — |
| DELETE | `/books/{id}` | Yes | — |
| GET | `/books/search-external` | No | 30/min |
| POST | `/books/import-external` | Yes | — |
| GET | `/authors` | No | — |
| POST | `/authors` | Yes | — |
| GET | `/authors/{id}` | No | — |
| DELETE | `/authors/{id}` | Yes | — |
| POST | `/auth/register` | No | — |
| POST | `/auth/login` | No | 5/min |
| GET | `/auth/me` | Yes | — |
| POST | `/reset-db` | **No auth — critical flaw** | — |

**Key patterns:**
- `@asynccontextmanager` lifespan creates tables + seeds (idempotent: checks `db.exec(select(Author)).first()` first)
- CORS: explicit list — `localhost:5173`, `localhost:5174`, `FRONTEND_URL` from env. `allow_credentials=True`, no wildcards
- `slowapi` `Limiter` with `jwt_or_ip_key`: reads `jose.jwt.get_unverified_claims()` on Auth header if present → `user:<sub>`, otherwise `ip:<client.host>`
- **Decorator order is critical:** `@app.post(...)` outer, `@limiter.limit(...)` inner — reversal silently disables the limit
- 429 handler returns `Retry-After: 60` header

---

### `models.py`

**`Author` (table=True):**
- `id: Optional[int]` — PK auto-increment
- `name: str` — Field(index=True, max_length=100)
- `bio: Optional[str]` — Field(max_length=500)
- `created_at: datetime` — default_factory=datetime.utcnow
- `books: List["Book"]` — Relationship(back_populates="author")

**`Book` (table=True):**
- `id: Optional[int]` — PK
- `title: str` — Field(index=True, max_length=200)
- `price: float` — Field(ge=0)
- `isbn: str` — Field(unique=True, max_length=13)
- `stock: int` — Field(default=0, ge=0)
- `genre: str` — Field(max_length=50)
- `author_id: int` — Field(foreign_key="author.id")
- `created_at: datetime`
- `author: Author` — Relationship(back_populates="books")

**`User` (table=True):**
- `id: Optional[int]` — PK
- `username: str` — Field(unique=True, index=True, max_length=50)
- `email: str` — Field(unique=True, index=True, max_length=100)
- `hashed_password: str` — Field(max_length=255)
- `created_at: datetime`

**No cascade deletes — integrity enforced in Python (AuthorService checks before delete).**

---

### `schemas.py`

- `AuthorCreate`: name (min 1, max 100), bio (optional, max 1000)
- `AuthorResponse`: id, name, bio, created_at — `ConfigDict(from_attributes=True)`
- `BookCreate`: title, author_id, isbn (optional, regex `^(\d{10}|\d{13})$`), price (gt=0), stock (ge=0), genre
- `BookUpdate`: all fields Optional — `model_dump(exclude_unset=True)` enables partial PUT
- `BookResponse`: all fields + nested `author: AuthorResponse`
- `ExternalBookResult`: title, author, year, isbn (all optional except title)
- `ImportBookRequest`: isbn (regex validated), author_name (optional)
- `UserCreate`: username (3–50 chars), email (EmailStr), password (min 8 chars)
- `UserLogin`: email (EmailStr), password
- `Token`: access_token, token_type="bearer"
- `UserResponse`: id, username, email, created_at — **hashed_password excluded**

---

### `auth_utils.py`

```python
def hash_password(password: str) -> str          # passlib bcrypt, embedded salt
def verify_password(plain: str, hashed: str) -> bool  # constant-time comparison
def create_access_token(data: dict) -> str        # adds exp claim, HS256 signs
def decode_access_token(token: str) -> dict       # raises JWTError on failure
```

Dependencies: `passlib[bcrypt]`, `python-jose[cryptography]`

---

### `config.py`

```python
SECRET_KEY = os.getenv("SECRET_KEY", "<hardcoded-dev-fallback>")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60
```

**Risk: hardcoded fallback means a missing `SECRET_KEY` env var in production allows anyone who reads this public repo to forge tokens.**

---

### `database.py`

```python
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///bytebooks.db")
if DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)
```

- SQLite: `connect_args={"check_same_thread": False}`, `echo=True`
- PostgreSQL: no connect args, `echo=False`
- `get_session()`: FastAPI `Depends` generator

---

### `dependencies.py`

```python
def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(HTTPBearer(auto_error=False)),
    session: Session = Depends(get_session),
) -> User:
```

Flow:
1. `auto_error=False` — returns `None` instead of auto-403 if no header
2. None credentials → 401
3. `decode_access_token(token)` → `JWTError` on bad/expired token → 401
4. Extract `sub` → `int(user_id)`
5. `session.get(User, user_id)` — handles deleted-user case → 401
6. All failures: identical 401 `"Could not validate credentials"` + `WWW-Authenticate: Bearer`

---

### `services.py`

**`BookService` (static methods):**
- `create_book`: verify author exists (404), check duplicate ISBN (409)
- `update_book`: check exists (404), validate price/stock (422), check ISBN uniqueness excluding self (409), apply `model_dump(exclude_unset=True)`
- `delete_book`, `get_book`: 404 if not found
- `list_books`: `db.exec(select(Book)).all()`

**`AuthorService` (static methods):**
- `create_author`: creates and commits
- `delete_author`: 404 if not found, 409 if author has books
- `list_authors`, `get_author`

**`UserService` (static methods):**
- `create_user`: check email (400), check username (400), hash password, create
- `authenticate`: fetch by email, `verify_password` — identical 401 for unknown email OR wrong password (no email enumeration)
- `get_by_id`: `db.get(User, user_id)`

---

### `external_api.py`

`OpenLibraryService` (async static methods):
- `search_books(query)`: GET openlibrary.org/search.json, timeout=5s
- `get_book_by_isbn(isbn)`: GET openlibrary.org/api/books

Error translation:
- `httpx.TimeoutException` → 504
- `httpx.NetworkError` → 503
- Non-200 from OL → 502
- ISBN key missing → 404

---

### `requirements.txt`

```
fastapi
uvicorn[standard]
sqlmodel
python-multipart
httpx>=0.24.0
passlib[bcrypt]
bcrypt<4.0          ← pin: passlib 1.7.4 incompatible with bcrypt 4.x
python-jose[cryptography]
pydantic[email]
psycopg2-binary
slowapi>=0.1.9
```

**No version pins for fastapi, sqlmodel, uvicorn — Railway builds may pick up breaking changes.**

---

### `Procfile`

```
web: uvicorn main:app --host 0.0.0.0 --port $PORT
```

Single worker — no gunicorn, no `--workers`. Fine for course project; inadequate for production traffic.

---

## Frontend — File by File

### `src/App.jsx` — Route Table

```
/login          → <LoginPage />              (outside DashboardLayout)
/register       → <RegisterPage />           (outside DashboardLayout)
<DashboardLayout>
  /             → <Dashboard />
  /books        → <BooksPage />
  /authors      → <AuthorsPage />
  /books/new    → <ProtectedRoute><AddBookPage /></ProtectedRoute>
</DashboardLayout>
```

---

### `src/contexts/AuthContext.jsx`

State: `user`, `token`, `loading`, `error`

- `login(email, password)`: POST `/auth/login` → store token in localStorage → GET `/auth/me` → populate `user`
- `register(username, email, password)`: POST `/auth/register` → auto-calls `login()` (no double entry)
- `logout()`: clear state + remove from localStorage
- **On mount**: reads localStorage token → GET `/auth/me` to validate (handles stale tokens on restart)
- `loading=true` during mount check — prevents ProtectedRoute flash-to-login on refresh

**Documented risk:** localStorage is XSS-accessible. Comments explicitly recommend httpOnly cookies for production.

---

### `src/utils/api.js` — `authFetch`

- Reads token from localStorage
- Adds `Authorization: Bearer <token>` header
- Prepends `VITE_API_URL` to path
- On 401 with existing token: removes token + `window.location.href = '/login'` (hard redirect)

---

### `src/components/ProtectedRoute.jsx`

1. If `loading` → spinner
2. If `!user` → `<Navigate to="/login" replace state={{ from: location }} />`
3. Otherwise → `children`

`replace` prevents back-button looping. `from` preserved for potential post-login redirect (not wired in LoginPage).

---

### `src/components/DashboardLayout.jsx`

- Fixed sidebar with `NavLink` (auto `active` class via callback)
- "Add Book" link only rendered when `user` is truthy
- Header: `Welcome, {user.username}` + initials avatar + Logout when auth; Login/Register otherwise
- `<Outlet />` for nested route content

---

### `src/components/BookList.jsx`

State: `books`, `loading`, `error`, `searchTerm`, `selectedGenre`, `selectedBook`, `mode`, `editingBook`

- Client-side filtering: title search (case-insensitive `.includes()`) + genre dropdown
- Genre dropdown from `[...new Set(books.map(b => b.genre))]`
- Edit/delete buttons passed as `undefined` to BookCard for unauthenticated users (cards hide buttons)
- `e.stopPropagation()` on edit/delete to prevent modal trigger
- `{selectedBook && <BookDetail />}` — unmounts on close

---

### `src/components/BookCard.jsx`

- `author?.name ?? "Unknown Author"` — optional chaining + nullish coalescing
- `price.toFixed(2)` formatting
- Genre badge only if truthy
- Edit/delete buttons only if handlers provided

---

### `src/components/BookDetail.jsx`

Modal overlay. Backdrop click closes; `e.stopPropagation()` on inner card. Shows price, genre, ISBN, stock ("Out of stock" for 0). Pure display — no state, no fetches.

---

### `src/components/AddBookForm.jsx`

1. `useEffect` on mount fetches `/authors`, pre-selects first as default
2. `handleChange` uses `e.target.name` as computed key — single handler for all fields
3. Client-side validation before POST
4. POST via `authFetch`, type-casts `price` and `stock` to numbers
5. Reset form + call `onBookAdded` on success

---

### `src/components/EditBookForm.jsx`

- Excludes `author_id` from PUT payload (not in `BookUpdate` schema)
- Only sends changed fields via `model_dump(exclude_unset=True)` equivalent
- Pre-populates from `book` prop

---

### `src/pages/Dashboard.jsx`

- `Promise.all([fetch /books, fetch /authors])` concurrently
- Computes: total books, total authors, inventory value (`sum price * stock`), low-stock items (stock < 10)
- Renders stat cards + books data table
- Delete via `authFetch` + 204 check

---

### `src/pages/LoginPage.jsx`

- Redirects authenticated users: `<Navigate to="/" replace />`
- Calls `AuthContext.login()`
- `role="alert"` div for errors (accessibility)
- Generic error — doesn't differentiate unknown email from wrong password (consistent with backend)

---

### `middleware.js` — Vercel Edge Middleware

```js
export const config = {
  matcher: '/((?!assets/|favicon\\.ico|vite\\.svg).*)',
};

export default function middleware(request) {
  const requestId = crypto.randomUUID();
  const url = new URL(request.url);

  // Admin gate — no real /admin route yet; defensive pre-provision
  if (url.pathname.startsWith('/admin')) {
    const session = readCookie(request.headers.get('cookie'), 'bb_session');
    if (!session) return new Response('unauthorized', { status: 401 });
  }

  return next({ headers: { 'x-request-id': requestId } });
}
```

Custom `readCookie()` parses `Cookie` header manually. Matcher excludes static assets.

---

## Security Implementation

### HTTP Security Headers (`vercel.json`)

```json
{
  "rewrites": [{ "source": "/(.*)", "destination": "/index.html" }],
  "headers": [{
    "source": "/(.*)",
    "headers": [
      { "key": "Content-Security-Policy",
        "value": "default-src 'self'; script-src 'self'; connect-src 'self' https://week12-web-programming-production.up.railway.app; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'; base-uri 'self'; form-action 'self'" },
      { "key": "Strict-Transport-Security", "value": "max-age=63072000; includeSubDomains; preload" },
      { "key": "X-Frame-Options", "value": "DENY" },
      { "key": "X-Content-Type-Options", "value": "nosniff" },
      { "key": "Referrer-Policy", "value": "strict-origin-when-cross-origin" },
      { "key": "Permissions-Policy", "value": "camera=(), microphone=(), geolocation=(), interest-cohort=()" }
    ]
  }]
}
```

| Header | Purpose |
|--------|---------|
| CSP | XSS allowlist — enforcing, not Report-Only |
| HSTS | Force HTTPS for 2 years + preload |
| X-Frame-Options: DENY | Clickjacking defense |
| X-Content-Type-Options: nosniff | MIME sniffing defense |
| Referrer-Policy | Prevents full URL leakage cross-origin |
| Permissions-Policy | Disables camera, mic, geolocation, FLoC |

**Known weakness:** `style-src 'unsafe-inline'` — documented open item (required by inline component styles).

---

### Backend Rate Limiting (slowapi)

- `POST /auth/login`: 5/min per `user:<jwt-sub>` or `ip:<client-ip>`
- `GET /books/search-external`: 30/min
- 429 response includes `Retry-After: 60`

### Vercel WAF

- Path: `^/(api|auth)/.*$`
- Algorithm: Fixed Window, 60s window, 60 requests
- Counting key: IP Address
- Action: 429

---

## Authentication Implementation — Full JWT Flow

**Registration:**
1. Client: `{ username, email, password }` → POST `/auth/register`
2. `UserService.create_user`: check email unique (400), check username unique (400), bcrypt hash, store
3. Returns `UserResponse` (no password)
4. Frontend auto-calls `login()` immediately

**Login (rate-limited 5/min):**
1. Client: `{ email, password }` → POST `/auth/login`
2. `UserService.authenticate`: lookup by email, `verify_password()`. Identical 401 for "unknown email" AND "wrong password"
3. `create_access_token({"sub": str(user.id)})` — HS256, 60-minute TTL
4. Returns `Token(access_token, token_type="bearer")`
5. Client: store in localStorage, GET `/auth/me`

**Protected Route Access:**
1. `authFetch` adds `Authorization: Bearer <token>` header
2. `get_current_user` dependency: `HTTPBearer(auto_error=False)` → `decode_access_token` → extract `sub` → DB lookup → return `User`
3. All failure paths: identical 401 + `WWW-Authenticate: Bearer`

**Token lifecycle:** TTL 60 min, HS256, no refresh token, rotation via `SECRET_KEY` change on Railway.

---

## Database / Models Summary

| Table | Key Constraints |
|-------|----------------|
| `author` | `name` indexed |
| `book` | `isbn` UNIQUE, `price` ge=0, `stock` ge=0, FK → author.id |
| `user` | `username` UNIQUE+indexed, `email` UNIQUE+indexed |

Relationship: `Author.books ↔ Book.author` — bidirectional one-to-many, no cascade delete.

**Issue:** `Book.isbn` UNIQUE + empty string fallback — only one book can have no ISBN. Use `Optional[str]`.

**Issue:** `datetime.utcnow` deprecated in Python 3.12+. Use `datetime.now(timezone.utc)`.

---

## Deployment Config

### Backend (Railway)
- `DATABASE_URL` — auto-injected by Railway Postgres
- `SECRET_KEY` — `openssl rand -hex 32`
- `FRONTEND_URL` — bare Vercel origin, no trailing slash
- Auto-deploys on `git push origin main`

### Frontend (Vercel)
- `VITE_API_URL` — bare Railway origin, no trailing slash
- Root Directory: `bytebooks-frontend`
- Requires manual `vercel deploy --prod` (GitHub integration not connected)

---

## Test Coverage

### Tested
- Backend: genre field created, defaulted, and updated (3 pytest tests)
- Frontend v1 Playwright (4 specs): navigation, book list, search/filter, card modal
- Frontend v2 Playwright (9 specs): all v1 + edit, delete, form validation, visual regression, author page
- `global-setup.ts` calls `POST /reset-db` before each run; 3 browsers (Chromium, Firefox, WebKit)

### NOT Tested
- Auth flows (register, login, logout, protected route redirect)
- JWT expiration, rate limiting (429), author CRUD via UI
- External API, error states (404/409/422), CORS preflight
- Security headers presence, `/admin` gate, database failure

---

## Gaps and Missing Features

### Critical
1. `POST /reset-db` has no authentication — anyone can wipe all data
2. Hardcoded `SECRET_KEY` fallback — public repo; anyone can forge tokens
3. No CI/CD — zero GitHub Actions

### Functional
4. No refresh token — hard logout after 60 min
5. No RBAC — all authenticated users identical
6. No email verification or password reset
7. No pagination — all records in single query
8. AuthorsPage read-only — no create/edit UI

### Missing for Bonus Points
9. No social login (zero OAuth)
10. No 2FA / MFA
11. No admin dashboard or role management
12. No alternative deployment (only Vercel + Railway)
13. No CI test automation

---

## Code Quality Assessment

### Patterns Worth Copying Directly
1. Service layer — thin routes, all logic in `services.py`
2. Uniform 401 for all auth failures — prevents email enumeration
3. `model_dump(exclude_unset=True)` — true partial update
4. `HTTPBearer(auto_error=False)` — controls exact error response
5. `jwt_or_ip_key` rate limiting — per-user when auth, per-IP when anonymous
6. `AuthProvider` on-mount token validation — prevents stale token confusion
7. `ProtectedRoute` loading spinner — prevents flash-to-login on refresh
8. Idempotent seeding — checks existing data before insert
9. `dependency_overrides` in test fixtures — correct test DB injection pattern
10. `BookResponse` with nested `AuthorResponse` — denormalized read in one API call
11. CORS no-wildcard + explicit origin list
12. `bcrypt<4.0` pin — handles passlib/bcrypt incompatibility
13. Vercel 6-header security config — copy `vercel.json` headers block directly

### Patterns to Improve in Our Project
1. Gate `POST /reset-db` behind env check (`if ENV != "production"`)
2. Remove hardcoded `SECRET_KEY` fallback — raise error if missing
3. Use `datetime.now(timezone.utc)` instead of `datetime.utcnow`
4. Use nullable `Optional[str]` for ISBN column
5. Pin all `requirements.txt` packages
6. Move JWT to httpOnly cookies + CSRF token
7. Add `offset`/`limit` pagination
8. Replace `window.location.href` on 401 with `useNavigate`
9. Add TypeScript to source files (not just tests)
