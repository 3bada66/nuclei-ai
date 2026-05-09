# NucleiAI — Web Platform

> AI-powered cell nuclei segmentation and counting as a full-stack web application.

Upload a histopathology image → get a segmentation mask, overlay, and nuclei count in seconds. Built for the Web Programming course with a complete auth system, role-based access control, automated tests, and cloud deployment.

---

## Feature Matrix

| Category | Feature | Status |
|---|---|---|
| **Core** | Image upload → U-Net inference → mask + overlay + count | ✅ |
| **Core** | Fallback Otsu-threshold demo (works without GPU/checkpoint) | ✅ |
| **Core** | Per-user job history with annotations | ✅ |
| **Auth** | JWT authentication (register / login / `/auth/me`) | ✅ |
| **Auth** | TOTP 2FA (Google Authenticator) | ✅ |
| **Auth** | Email OTP (second 2FA method) | ✅ +5 pts |
| **Auth** | Google OAuth | ✅ |
| **Auth** | GitHub OAuth | ✅ +5 pts |
| **Auth** | Dropbox OAuth | ✅ +10 pts |
| **Authorization** | RBAC: `admin` / `researcher` / `viewer` roles | ✅ +10 pts |
| **Authorization** | Admin dashboard — user list, role editor, delete, stats | ✅ |
| **Core** | CSV export of job history (streaming download) | ✅ |
| **Core** | Dashboard search, mode filter, and pagination | ✅ |
| **Core** | 7-day cell-count trend chart (pure SVG, no library) | ✅ |
| **Testing** | 85 pytest backend unit tests (6 suites) | ✅ +15 pts |
| **Testing** | 17 Playwright E2E tests (auth, nav, CRUD, admin) | ✅ |
| **Testing** | GitHub Actions CI/CD (test → build → deploy) | ✅ |
| **Deployment** | Dockerfile + Fly.io config (`fly.toml`) | ✅ +10 pts |
| **Deployment** | Cloudflare Pages (`_redirects`, `_headers`) | ✅ |
| **Security** | HTTP security headers middleware (CSP, HSTS, X-Frame-Options…) | ✅ |
| **Security** | Image magic-bytes validation (not just `Content-Type`) | ✅ |
| **Security** | Cryptographically secure OTP (`secrets` module) | ✅ |
| **Security** | Rate limiting on all auth and analysis endpoints | ✅ |
| **Security** | Password strength validation (letters + digits required) | ✅ |
| **Security** | API docs disabled in production | ✅ |
| **Security** | `pip-audit` dependency scan in CI | ✅ |

**Estimated bonus: +55 points**

---

## Architecture

```mermaid
graph TD
    Browser["Browser (React + Vite)"]
    CF["Cloudflare Pages"]
    API["FastAPI (Fly.io)"]
    DB["SQLite / PostgreSQL (SQLModel)"]
    Storage["File Storage (Fly volume)"]
    ML["Analysis Service\nU-Net or Otsu fallback"]

    Browser -->|HTTPS| CF
    CF -->|static assets| Browser
    Browser -->|REST + JWT| API
    API -->|ORM| DB
    API -->|read/write| Storage
    API -->|analyze()| ML
    ML -->|mask · overlay · count| API
```

### Request flow — image analysis

```
POST /api/analyze  (multipart, Bearer token)
  │
  ├─ 1. JWT validation (get_current_user)
  ├─ 2. Content-Type + magic-bytes check
  ├─ 3. analysis_service.analyze(bytes, filename)
  │      ├─ _ensure_model_loaded()  →  U-Net or Otsu fallback
  │      ├─ decode + resize to 256×256
  │      ├─ predict mask
  │      ├─ make_overlay()
  │      ├─ count_nuclei_from_binary()
  │      └─ write {job_id}_input / _mask / _overlay .png
  ├─ 4. JobService.create_job()  →  INSERT AnalysisJob
  └─ 5. 201 AnalysisResponse {job_id, cell_count, urls, metadata}
```

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router v6 |
| Backend | FastAPI, Python 3.12, SQLModel, Uvicorn |
| Database | SQLite (dev) / PostgreSQL (prod) |
| Auth | python-jose JWT, passlib bcrypt, pyotp TOTP, authlib OAuth |
| AI | OpenCV (fallback) + U-Net via torch + segmentation_models_pytorch |
| Rate limiting | slowapi |
| Testing — backend | pytest, FastAPI TestClient, in-memory SQLite |
| Testing — E2E | Playwright (Chromium) |
| CI/CD | GitHub Actions |
| Backend hosting | Fly.io |
| Frontend hosting | Cloudflare Pages |

---

## Local Development

### Prerequisites

- Python 3.12+
- Node.js 20+

### 1 — Backend

```sh
# From web-programming/
pip install -r backend/requirements.txt

uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

Backend: `http://127.0.0.1:8000`  
Swagger UI: `http://127.0.0.1:8000/docs`

### 2 — Frontend

```sh
cd frontend
npm install
npm run dev       # .env.development already sets VITE_API_URL
```

Frontend: `http://localhost:5173`

### First login

The **first registered user** is automatically promoted to `admin`. All subsequent registrations become `viewer`.

---

## Database Schema

```
User
  id · username · email · hashed_password · role (admin|researcher|viewer)
  totp_secret · totp_enabled
  email_otp_hash · email_otp_expires_at · created_at

AnalysisJob
  id · job_id (12-char hex) · user_id (FK→User)
  status · cell_count · mode · original_filename
  input_url · mask_url · overlay_url
  processing_ms · threshold · min_area · image_size · device · created_at

Annotation
  id · job_id (FK→AnalysisJob) · user_id (FK→User) · note · created_at
```

---

## API Reference

| Method | Path | Auth | Description |
|---|---|---|---|
| GET | `/health` | — | Liveness probe |
| GET | `/api/health` | — | Full health payload |
| POST | `/auth/register` | — | Create account (first user → admin) |
| POST | `/auth/login` | — | Password login; returns JWT or `requires_2fa` |
| GET | `/auth/me` | JWT | Current user profile |
| PATCH | `/auth/me` | JWT | Update username / email |
| POST | `/auth/change-password` | JWT | Change password (requires current password) |
| POST | `/auth/2fa/setup` | JWT | Generate TOTP secret + provisioning URI |
| POST | `/auth/2fa/verify-setup` | JWT | Confirm TOTP code and enable 2FA |
| POST | `/auth/2fa/verify` | temp JWT | Complete 2FA login → full JWT |
| POST | `/auth/email-otp/send` | — | Send 6-digit code to email |
| POST | `/auth/email-otp/verify` | — | Verify code → JWT |
| GET | `/auth/google` | — | Redirect to Google OAuth |
| GET | `/auth/github` | — | Redirect to GitHub OAuth |
| GET | `/auth/dropbox` | — | Redirect to Dropbox OAuth |
| POST | `/api/analyze` | JWT | Upload image → 201 analysis result |
| GET | `/api/jobs` | JWT | List jobs (admin sees all) |
| GET | `/api/jobs/export.csv` | JWT | Download job history as CSV |
| GET | `/api/jobs/{job_id}` | JWT | Job detail + annotations |
| DELETE | `/api/jobs/{job_id}` | JWT | Delete job |
| POST | `/api/jobs/{job_id}/annotations` | JWT | Add annotation |
| GET | `/api/jobs/{job_id}/annotations` | JWT | List annotations |
| DELETE | `/api/annotations/{id}` | JWT | Delete annotation |
| GET | `/files/{filename}` | — | Serve result image |
| GET | `/admin/users` | admin | List all users |
| PATCH | `/admin/users/{id}/role` | admin | Change user role |
| DELETE | `/admin/users/{id}` | admin | Delete user |
| GET | `/admin/stats` | admin | Platform statistics |

---

## Authentication Flows

### Password login — no 2FA
```
POST /auth/login  →  200 { access_token, user }
```

### Password login — TOTP 2FA enabled
```
POST /auth/login         →  200 { requires_2fa: true, temp_token }
POST /auth/2fa/verify    →  200 { access_token, user }
  (Bearer: temp_token, body: { code: "123456" })
```

### Email OTP
```
POST /auth/email-otp/send    { email }            →  200
POST /auth/email-otp/verify  { email, code }      →  200 { access_token, user }
```

### OAuth (Google / GitHub / Dropbox)
```
GET /auth/{provider}           →  302 to provider
GET /auth/{provider}/callback  →  302 to /oauth-callback?token=<jwt>
```

---

## Running Tests

### Backend (85 tests)

```sh
# From web-programming/
python -m pytest backend/tests/ -v
```

| Suite | Tests | Coverage |
|---|---|---|
| `test_auth.py` | 14 | Register, login, JWT, identical-error guarantee |
| `test_crud.py` | 15 | Analyze, jobs, annotations, file validation |
| `test_roles.py` | 11 | RBAC, admin endpoints |
| `test_totp.py` | 10 | Full 2FA flow, token scope checks |
| `test_export.py` | 8 | CSV export, content-type, RBAC scoping, field values |
| `test_security.py` | 15 | Magic bytes, headers, password strength |
| `test_profile.py` | 12 | Update username/email, conflict checks, change-password |

### E2E (17 tests)

```sh
# Start backend and frontend first, then:
cd frontend && npx playwright test
```

| Suite | Tests |
|---|---|
| `auth.spec.ts` | 6 |
| `navigation.spec.ts` | 4 |
| `crud.spec.ts` | 3 |
| `admin.spec.ts` | 4 |

---

## Deployment

### Backend → Fly.io

```sh
cd web-programming

fly launch --no-deploy
fly postgres create --name nuclei-db && fly postgres attach nuclei-db
fly volumes create nuclei_storage --region iad --size 1

fly secrets set \
  SECRET_KEY="$(openssl rand -hex 32)" \
  FRONTEND_URL="https://<pages-project>.pages.dev" \
  ENV="production"

fly deploy
```

### Frontend → Cloudflare Pages

| Setting | Value |
|---|---|
| Build command | `npm run build` |
| Build output directory | `dist` |
| Root directory | `web-programming/frontend` |
| `VITE_API_URL` env var | `https://nuclei-ai-backend.fly.dev` |

---

## Project Structure

```
web-programming/
├── backend/
│   ├── main.py              FastAPI app — all routes
│   ├── models.py            SQLModel ORM tables
│   ├── schemas.py           Pydantic DTOs
│   ├── config.py            Environment config
│   ├── database.py          Engine + session
│   ├── dependencies.py      get_current_user, require_role
│   ├── auth_utils.py        JWT · bcrypt · OTP · SMTP
│   ├── totp_utils.py        pyotp helpers
│   ├── oauth.py             authlib Google/GitHub/Dropbox
│   ├── security.py          SecurityHeadersMiddleware · magic-bytes
│   ├── crud.py              JobService · AnnotationService
│   ├── services/
│   │   └── analysis_service.py
│   ├── requirements.txt
│   └── tests/               conftest + 6 test modules
├── frontend/
│   ├── src/
│   │   ├── App.tsx          Route table
│   │   ├── api.ts           All API calls + TS types
│   │   ├── contexts/        AuthContext · ToastContext
│   │   ├── components/      DashboardLayout · ProtectedRoute · AdminRoute ·
│   │   │                    ConfirmModal · ToastContainer · TrendChart
│   │   └── pages/           Login · Register · Dashboard · Analyze ·
│   │                        JobDetail · TwoFactorSetup · TwoFactorVerify ·
│   │                        OAuthCallback · Admin · Profile
│   ├── e2e/                 Playwright specs
│   ├── public/
│   │   ├── _redirects       SPA catch-all
│   │   └── _headers         Security headers
│   └── playwright.config.ts
├── src/                     Original ML pipeline
├── Dockerfile
├── fly.toml
└── .dockerignore
```

---

## Environment Variables

### Backend

| Variable | Default | Required in prod |
|---|---|---|
| `SECRET_KEY` | dev fallback | **yes** |
| `DATABASE_URL` | `sqlite:///./nuclei.db` | yes (Postgres URL) |
| `ENV` | `development` | set to `production` |
| `FRONTEND_URL` | `http://localhost:5173` | yes |
| `ACCESS_TOKEN_EXPIRE_MINUTES` | `60` | no |
| `GOOGLE_CLIENT_ID` / `_SECRET` | empty | for Google OAuth |
| `GITHUB_CLIENT_ID` / `_SECRET` | empty | for GitHub OAuth |
| `DROPBOX_CLIENT_ID` / `_SECRET` | empty | for Dropbox OAuth |
| `SMTP_HOST/PORT/USER/PASSWORD` | gmail defaults | for Email OTP |

### Frontend

| Variable | Default |
|---|---|
| `VITE_API_URL` | `http://127.0.0.1:8000` |
