# Web Programming Project — Implementation Plan
> Based on: project_requirements + week12 reference analysis
> Date: 2026-05-06

---

## Scoring Map (maximize before you start)

| Requirement | Points | Our Target |
|---|---|---|
| Core (DB + FastAPI + Frontend + Validation + Entities) | Base | ✅ All covered |
| Playwright testing | Full | ✅ |
| 90%+ coverage with unit tests | +5 | ✅ |
| Automated tests with each deployment | +10 | ✅ GitHub Actions |
| Social login × 1 | Full | ✅ Google |
| Social login × 2 | +5 | ✅ GitHub |
| Social login × 3 | +10 | ✅ Discord or Microsoft |
| Basic Auth + 2FA × 1 | Full | ✅ TOTP (Google Authenticator) |
| Basic Auth + 2FA × 2 | +5 | ✅ Email OTP |
| Authorization (roles + admin dashboard) | +10 | ✅ |
| Alternative deployment (not Vercel/Railway) | +10 | ✅ Fly.io + Cloudflare Pages |
| Securing the servers | Required | ✅ |
| Using old project as base | Full | ✅ week12 as base |

**Max reachable bonus: +50 points on top of base grade**

---

## Tech Stack Decisions

### Backend
- **FastAPI** + **SQLModel** + **PostgreSQL**
- **passlib[bcrypt]** — password hashing
- **python-jose** — JWT tokens
- **pyotp** — TOTP 2FA
- **authlib** — OAuth2 social login (Google, GitHub, Discord)
- **slowapi** — rate limiting
- **httpx** — async HTTP (external APIs)
- **pytest** — unit tests

### Frontend
- **React 19** + **Vite** + **React Router v6**
- **TypeScript** throughout (upgrade from week12's JSX)
- Plain CSS (no UI library — keeps it lightweight and explainable)

### Deployment (bonus: alternative to Vercel + Railway)
- **Backend → Fly.io** (Docker-based, free tier, full control)
- **Frontend → Cloudflare Pages** (faster CDN than Vercel, free tier)
- **Database → Fly.io Postgres** (managed, same network as app)

### Testing
- **Playwright** — E2E tests
- **pytest** — backend unit tests
- **GitHub Actions** — CI/CD pipeline (runs both on every push)

---

## Project Structure (Backend)

```
backend/
├── main.py              ← thin routes only
├── models.py            ← SQLModel ORM tables
├── schemas.py           ← Pydantic request/response DTOs
├── services.py          ← all business logic
├── auth_utils.py        ← hash, verify, create/decode JWT
├── oauth.py             ← Google / GitHub / Discord OAuth flows
├── totp_utils.py        ← pyotp TOTP generation and verification
├── dependencies.py      ← get_current_user, require_role()
├── config.py            ← env var loading (no hardcoded fallbacks)
├── database.py          ← dual SQLite/PostgreSQL engine
├── external_api.py      ← any external API calls
├── requirements.txt     ← all packages pinned
├── Dockerfile           ← for Fly.io deployment
├── fly.toml             ← Fly.io config
├── .env.example
└── tests/
    ├── conftest.py      ← in-memory SQLite fixtures, dependency_overrides
    ├── test_auth.py
    ├── test_crud.py
    ├── test_roles.py
    └── test_totp.py
```

## Project Structure (Frontend)

```
frontend/
├── src/
│   ├── App.tsx
│   ├── main.tsx
│   ├── components/
│   │   ├── DashboardLayout.tsx
│   │   ├── ProtectedRoute.tsx
│   │   ├── AdminRoute.tsx       ← wraps admin-only pages
│   │   └── ...
│   ├── contexts/
│   │   └── AuthContext.tsx
│   ├── pages/
│   │   ├── LoginPage.tsx
│   │   ├── RegisterPage.tsx
│   │   ├── TwoFactorPage.tsx    ← TOTP entry after login
│   │   ├── AdminPage.tsx        ← user management + role editor
│   │   └── ...
│   └── utils/
│       └── api.ts               ← authFetch wrapper
├── vercel.json                  ← NOT used (Cloudflare Pages instead)
├── _headers                     ← Cloudflare Pages security headers
├── package.json
└── tests/
    ├── playwright.config.ts
    ├── global-setup.ts          ← POST /reset-db
    └── specs/
        ├── auth.spec.ts
        ├── navigation.spec.ts
        ├── crud.spec.ts
        ├── admin.spec.ts
        ├── totp.spec.ts
        └── visual.spec.ts
```

---

## Phase 1 — Foundation (Days 1–3)

**Goal:** Running full-stack app with core domain models and CRUD.

### 1.1 Set up from week12 base
- [ ] Copy `bytebooks-api` backend structure (all 8 files)
- [ ] Copy `bytebooks-frontend` React structure
- [ ] Replace all "ByteBooks" domain names with your project domain
- [ ] Upgrade frontend `.jsx` files to `.tsx` (TypeScript)
- [ ] Verify dev environment works: `uvicorn main:app --reload` + `npm run dev`

### 1.2 Define your entities
Design your domain models. Every project needs at least 3 related tables.  
Example structure (adapt to your domain):

```
User (id, username, email, hashed_password, role, totp_secret, created_at)
  ↓ one-to-many
[YourMainEntity] (id, user_id FK, ...fields, created_at)
  ↓ one-to-many or many-to-many
[YourSubEntity] (id, parent_id FK, ...fields)
```

- [ ] Write `models.py` with all tables, relationships, Field constraints
- [ ] Write `schemas.py` with Create/Update/Response DTOs for each entity
- [ ] Write `services.py` with CRUD static methods for each entity
- [ ] Wire routes in `main.py` (GET, POST, PUT, DELETE per entity)
- [ ] Test all endpoints at `http://localhost:8000/docs`

### 1.3 Core frontend
- [ ] Set up React Router v6 route table in `App.tsx`
- [ ] Build `DashboardLayout` with sidebar + `<Outlet />`
- [ ] Build list page and detail/edit page for each main entity
- [ ] Wire `authFetch` utility with `VITE_API_URL`
- [ ] CORS configured in FastAPI for `localhost:5173`

**Checkpoint:** Full CRUD works end-to-end in the browser.

---

## Phase 2 — Authentication (Days 4–6)

**Goal:** JWT login, Google OAuth, GitHub OAuth, Discord OAuth, TOTP 2FA, email OTP.

### 2.1 Basic JWT Auth (from week12 — copy directly)
- [ ] `User` model with `username`, `email`, `hashed_password`, `role`, `totp_secret`, `totp_enabled`
- [ ] `auth_utils.py`: `hash_password`, `verify_password`, `create_access_token`, `decode_access_token`
- [ ] `config.py`: `SECRET_KEY` — **no hardcoded fallback**, raise `ValueError` if missing
- [ ] `POST /auth/register` — bcrypt hash, store user
- [ ] `POST /auth/login` — verify, return JWT (or trigger 2FA flow if enabled)
- [ ] `GET /auth/me` — protected, return current user
- [ ] `dependencies.py`: `get_current_user` with `HTTPBearer(auto_error=False)`
- [ ] Frontend: `AuthContext.tsx`, `ProtectedRoute.tsx`, `LoginPage`, `RegisterPage`

### 2.2 TOTP 2FA (Google Authenticator) — *Auth bonus ×1*
```python
# totp_utils.py
import pyotp, qrcode, base64

def generate_totp_secret() -> str:
    return pyotp.random_base32()

def get_totp_uri(secret: str, email: str, issuer: str) -> str:
    return pyotp.totp.TOTP(secret).provisioning_uri(email, issuer_name=issuer)

def verify_totp(secret: str, code: str) -> bool:
    return pyotp.TOTP(secret).verify(code, valid_window=1)
```

- [ ] `POST /auth/2fa/setup` — generate secret, return QR code as base64 PNG
- [ ] `POST /auth/2fa/verify-setup` — confirm code, set `totp_enabled=True`, store encrypted secret
- [ ] Modify `POST /auth/login`: if `totp_enabled`, return `{ requires_2fa: true, temp_token }` instead of full JWT
- [ ] `POST /auth/2fa/verify` — accept temp_token + TOTP code, return full JWT
- [ ] Frontend: `TwoFactorSetupPage` (show QR + input), `TwoFactorVerifyPage` (code entry on login)

### 2.3 Email OTP — *Auth bonus ×2*
- [ ] Add `smtplib` or use `sendgrid`/`resend` for email sending
- [ ] `POST /auth/email-otp/send` — generate 6-digit code, store hashed in DB with 10-min TTL
- [ ] `POST /auth/email-otp/verify` — verify code, issue JWT
- [ ] Frontend: Email OTP option on login page

### 2.4 Google OAuth — *Social login ×1* (full points)
```python
# oauth.py — using authlib
from authlib.integrations.starlette_client import OAuth

oauth = OAuth()
oauth.register(
    name='google',
    client_id=GOOGLE_CLIENT_ID,
    client_secret=GOOGLE_CLIENT_SECRET,
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'},
)
```

- [ ] `GET /auth/google` — redirect to Google consent screen
- [ ] `GET /auth/google/callback` — exchange code, upsert user, return JWT
- [ ] Frontend: "Sign in with Google" button on `LoginPage`

### 2.5 GitHub OAuth — *Social login ×2* (+5)
- [ ] `GET /auth/github` — redirect to GitHub OAuth
- [ ] `GET /auth/github/callback` — exchange code, upsert user, return JWT
- [ ] Frontend: "Sign in with GitHub" button

### 2.6 Discord OAuth — *Social login ×3* (+10)
- [ ] `GET /auth/discord` — redirect to Discord OAuth
- [ ] `GET /auth/discord/callback` — exchange code, upsert user, return JWT
- [ ] Frontend: "Sign in with Discord" button

**Checkpoint:** All 5 auth methods work in the browser.

---

## Phase 3 — Authorization & Admin Dashboard (Days 7–8)

**Goal:** Multiple user roles, different permissions, admin UI that changes them dynamically.
This earns the **+10 authorization bonus**.

### 3.1 Role System
```python
# models.py — add to User
class UserRole(str, enum.Enum):
    admin = "admin"
    editor = "editor"
    viewer = "viewer"

class User(SQLModel, table=True):
    ...
    role: UserRole = Field(default=UserRole.viewer)
```

### 3.2 Role-based dependencies
```python
# dependencies.py
def require_role(*roles: UserRole):
    def checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in roles:
            raise HTTPException(status_code=403, detail="Insufficient permissions")
        return current_user
    return checker

# Usage in main.py:
@app.delete("/items/{id}")
def delete_item(id: int, user=Depends(require_role(UserRole.admin, UserRole.editor))):
    ...
```

### 3.3 Admin API endpoints
- [ ] `GET /admin/users` — list all users with roles (admin only)
- [ ] `PATCH /admin/users/{id}/role` — change user role dynamically (admin only)
- [ ] `DELETE /admin/users/{id}` — delete user (admin only)
- [ ] `GET /admin/stats` — usage statistics

### 3.4 Admin Dashboard (frontend)
- [ ] `AdminRoute.tsx` — wraps admin pages, redirects non-admins
- [ ] `AdminPage.tsx` — user table with role dropdown per row
- [ ] Role dropdown: `viewer` → `editor` → `admin` — saves on change via `PATCH /admin/users/{id}/role`
- [ ] Stats panel: total users by role, activity counts
- [ ] Add `/admin` to sidebar, visible only when `user.role === 'admin'`

**Checkpoint:** Admin can change any user's role from the UI and it takes effect immediately on their next request.

---

## Phase 4 — Testing (Days 9–11)

**Goal:** 90%+ Playwright coverage + pytest backend tests + GitHub Actions automation.

### 4.1 Backend unit tests (pytest)
```python
# tests/conftest.py
@pytest.fixture
def session():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False},
                           poolclass=StaticPool)
    SQLModel.metadata.create_all(engine)
    with Session(engine) as session:
        yield session

@pytest.fixture
def client(session):
    app.dependency_overrides[get_session] = lambda: session
    yield TestClient(app)
    app.dependency_overrides.clear()
```

Write tests for:
- [ ] `test_auth.py` — register, login, duplicate email, wrong password, JWT expiry
- [ ] `test_totp.py` — setup, verify correct code, reject wrong code
- [ ] `test_crud.py` — create, read, update, delete for each entity; 404s and 409s
- [ ] `test_roles.py` — viewer blocked from editor routes, editor blocked from admin routes
- [ ] `test_rate_limit.py` — 6th login attempt within 1 min → 429

### 4.2 Playwright E2E tests
Add `POST /reset-db` endpoint (env-gated: only in non-production):
```python
@app.post("/reset-db", include_in_schema=False)
def reset_db(session: Session = Depends(get_session)):
    if os.getenv("ENV") == "production":
        raise HTTPException(status_code=403)
    for table in reversed(SQLModel.metadata.sorted_tables):
        session.exec(text(f"DELETE FROM {table.name}"))
    session.commit()
    _seed_data(session)
```

Write specs covering:
- [ ] `auth.spec.ts` — register, login, logout, redirect to login if unauthenticated, TOTP flow
- [ ] `navigation.spec.ts` — sidebar links, active state, protected routes
- [ ] `crud.spec.ts` — create item, edit item, delete item (with dialog confirm)
- [ ] `admin.spec.ts` — admin sees admin panel, viewer does not; role change updates UI
- [ ] `search-filter.spec.ts` — search reduces results, clear restores
- [ ] `visual.spec.ts` — screenshot regression for key pages
- [ ] `error-states.spec.ts` — 404 page, form validation messages

`global-setup.ts`:
```typescript
import { chromium } from '@playwright/test';
export default async function globalSetup() {
  const browser = await chromium.launch();
  const page = await browser.newPage();
  await page.request.post('http://localhost:8000/reset-db');
  await browser.close();
}
```

### 4.3 GitHub Actions CI/CD — *+10 bonus*
```yaml
# .github/workflows/test.yml
name: Test & Deploy

on:
  push:
    branches: [main]
  pull_request:

jobs:
  backend-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install -r backend/requirements.txt
      - run: pytest backend/tests/ -v --cov=backend --cov-report=term

  e2e-tests:
    runs-on: ubuntu-latest
    needs: backend-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
      - uses: actions/setup-node@v4
        with: { node-version: '20' }
      - run: pip install -r backend/requirements.txt
      - run: uvicorn main:app &
        working-directory: backend
      - run: npm ci && npx playwright install --with-deps
        working-directory: frontend
      - run: npx playwright test
        working-directory: frontend

  deploy:
    runs-on: ubuntu-latest
    needs: e2e-tests
    if: github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: superfly/flyctl-actions/setup-flyctl@master
      - run: flyctl deploy --remote-only
        working-directory: backend
        env:
          FLY_API_TOKEN: ${{ secrets.FLY_API_TOKEN }}
```

**Checkpoint:** Every `git push` to main runs all tests, then deploys automatically only if they pass.

---

## Phase 5 — Deployment (Days 12–13)

**Goal:** Live production app on Fly.io + Cloudflare Pages. This earns the **+10 alternative deployment bonus**.

### 5.1 Backend — Fly.io

Why Fly.io over Railway:
- Docker-based (you control the full runtime)
- Private networking between app and DB (no public DB exposure)
- Built-in secrets management
- Free allowance sufficient for course project

```dockerfile
# backend/Dockerfile
FROM python:3.12-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

```toml
# backend/fly.toml
app = "your-app-name"
primary_region = "ams"

[http_service]
  internal_port = 8080
  force_https = true

[env]
  ENV = "production"
```

- [ ] `fly launch` — creates app and postgres
- [ ] `fly secrets set SECRET_KEY=... GOOGLE_CLIENT_ID=... GITHUB_CLIENT_ID=...`
- [ ] `fly deploy`
- [ ] Verify at `https://your-app-name.fly.dev/docs`

### 5.2 Frontend — Cloudflare Pages

Why Cloudflare Pages over Vercel:
- 500 builds/month free (vs Vercel's 100)
- Global CDN with better latency in more regions
- Security headers via `_headers` file (native, no JSON config)
- Zero cold starts

```
# frontend/public/_headers
/*
  Content-Security-Policy: default-src 'self'; script-src 'self'; connect-src 'self' https://your-app-name.fly.dev; img-src 'self' data:; style-src 'self' 'unsafe-inline'; frame-ancestors 'none'
  Strict-Transport-Security: max-age=63072000; includeSubDomains; preload
  X-Frame-Options: DENY
  X-Content-Type-Options: nosniff
  Referrer-Policy: strict-origin-when-cross-origin
  Permissions-Policy: camera=(), microphone=(), geolocation=()
```

- [ ] Connect GitHub repo to Cloudflare Pages
- [ ] Set Build command: `npm run build`, Output directory: `dist`
- [ ] Set env var: `VITE_API_URL=https://your-app-name.fly.dev`
- [ ] Auto-deploys on every `git push` to main
- [ ] Verify security headers with `curl -I https://your-pages-domain.pages.dev`

**Checkpoint:** `https://your-pages-domain.pages.dev` is live, secured, and connected to the backend.

---

## Phase 6 — Security Hardening (Day 14)

**Goal:** Pass the professor's attack. Take screenshots for the presentation.

### 6.1 Backend security
- [ ] **Rate limiting** (slowapi):
  - `POST /auth/login`: 5/min
  - `POST /auth/register`: 10/min
  - `POST /auth/email-otp/send`: 3/min
  - All routes: 100/min global
- [ ] **No hardcoded secrets** — `config.py` raises `ValueError` if any required env var is missing
- [ ] **CORS** — explicit origin list only, no `*`
- [ ] **`/reset-db` gated** — returns 403 if `ENV=production`
- [ ] **`datetime.now(timezone.utc)`** everywhere (not deprecated `utcnow`)
- [ ] **`/admin` endpoints** — gated with `require_role(UserRole.admin)`
- [ ] **SQL injection** — SQLModel parameterized queries (no raw string formatting)
- [ ] **Dependency audit** — `pip-audit -r requirements.txt` must show 0 vulnerabilities
- [ ] **`fly secrets`** — all secrets set as Fly.io secrets, none in code or fly.toml

### 6.2 Frontend security (Cloudflare `_headers`)
- [ ] CSP, HSTS, X-Frame-Options, X-Content-Type-Options, Referrer-Policy, Permissions-Policy
- [ ] Verify with securityheaders.com — target A or A+ rating
- [ ] JWT in httpOnly cookies (upgrade from localStorage) + CSRF token

### 6.3 Screenshots to take for presentation
- [ ] Fly.io dashboard showing app running
- [ ] Fly.io secrets page (keys visible, values hidden)
- [ ] securityheaders.com A+ result
- [ ] Rate limit 429 response in browser devtools
- [ ] `pip-audit` output showing 0 vulnerabilities
- [ ] GitHub Actions green CI run showing tests passed before deploy
- [ ] Cloudflare Pages dashboard showing deployment

---

## Phase 7 — Presentation Prep (Day 15)

For the **40% technical explanation** portion, be ready to explain every element live:

### Database
- Which ORM (SQLModel), which DB (PostgreSQL on Fly.io)
- Show the entity-relationship diagram
- Explain each table, field constraints (`Field(ge=0)`, `unique=True`), and relationships
- Explain the dual SQLite (dev) / PostgreSQL (prod) pattern in `database.py`

### FastAPI Backend
- Walk through the 8-file layered architecture
- Show how a request flows: route → service → model → DB
- Show Swagger UI at `/docs`
- Explain `Depends(get_current_user)` and `Depends(require_role(...))`

### Frontend
- React Router v6 route table
- `AuthContext` and how state flows through the app
- `ProtectedRoute` and `AdminRoute` components
- How `authFetch` attaches the JWT

### Validation
- Pydantic field constraints (`EmailStr`, `min_length`, `ge=0`, regex patterns)
- Schema separation: `UserCreate` vs `UserResponse` (why `hashed_password` is excluded)
- Client-side validation as UX, server-side as enforcement

### Entities and Relations
- Draw the ER diagram live
- Explain FK constraints and `Relationship(back_populates=...)`
- Explain why no cascade delete and how integrity is enforced in Python

### Auth methods (explain all 5)
- Basic JWT: bcrypt, HS256, 60-min TTL, `sub` claim
- TOTP: `pyotp`, QR code setup, `valid_window=1` for clock drift
- Email OTP: 6-digit code, hashed in DB, 10-min TTL
- Google/GitHub/Discord OAuth: `authlib`, code exchange, user upsert

### Testing
- Show GitHub Actions CI run
- Show Playwright test execution
- Explain `/reset-db` pattern for test isolation
- Show coverage report

### Deployment
- Explain why Fly.io over Railway (Docker, private networking, secrets management)
- Explain why Cloudflare Pages over Vercel (CDN, `_headers` file, build limits)
- Show the `Dockerfile` and `fly.toml`

### Security
- Show `securityheaders.com` result
- Explain each security header and what attack it prevents
- Show rate limiting in action (429 response)
- Explain the `jwt_or_ip_key` rate limit bucketing strategy

---

## Daily Schedule

| Day | Focus |
|-----|-------|
| 1 | Set up from week12 base, define entities, models.py + schemas.py |
| 2 | services.py + routes in main.py, test at /docs |
| 3 | React frontend: layout, list pages, CRUD wired end-to-end |
| 4 | Basic JWT auth (register/login), AuthContext, ProtectedRoute |
| 5 | TOTP 2FA setup + verify flow |
| 6 | Google OAuth + GitHub OAuth + Discord OAuth |
| 7 | Email OTP (2nd auth method) |
| 8 | User roles (admin/editor/viewer) + admin dashboard |
| 9 | pytest unit tests (backend) |
| 10 | Playwright E2E tests |
| 11 | GitHub Actions CI/CD pipeline |
| 12 | Fly.io backend deployment |
| 13 | Cloudflare Pages frontend deployment |
| 14 | Security hardening + screenshots |
| 15 | Presentation prep + run-through |

---

## Critical Rules (learned from week12 mistakes)

1. **No hardcoded `SECRET_KEY` fallback** — raise `ValueError` if env var missing
2. **Gate `/reset-db`** — `if os.getenv("ENV") == "production": raise 403`
3. **Use `datetime.now(timezone.utc)`** not deprecated `datetime.utcnow()`
4. **Nullable ISBN equivalent** — use `Optional[str]` for any field that's unique but optional
5. **Pin all packages** in `requirements.txt` — run `pip freeze > requirements.txt` before deploying
6. **Decorator order with slowapi** — `@app.post(...)` outer, `@limiter.limit(...)` inner
7. **CORS no trailing slash** — `FRONTEND_URL` must be `https://domain.com` not `https://domain.com/`
8. **`model_dump(exclude_unset=True)`** on all update endpoints — true partial updates
9. **Identical error for wrong email vs wrong password** — never reveal which is wrong
10. **Test auth flows in Playwright** — week12 had zero auth tests; we need them for 90%+ coverage
