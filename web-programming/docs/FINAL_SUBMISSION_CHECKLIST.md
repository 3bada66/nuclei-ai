# Final Submission Checklist

**Project:** AI-Powered Microscopy Analysis System — Web Platform  
**Course:** Web Programming  
**Sign-off rule:** all four members tick their items before the deadline.

---

## A. Core Web Application

- [x] FastAPI backend with SQLModel ORM (SQLite dev / PostgreSQL prod)
- [x] Three database tables: `User`, `AnalysisJob`, `Annotation` with FK relations
- [x] React + Vite + TypeScript frontend
- [x] REST API with Pydantic schemas (DTOs separate from ORM models)
- [x] Image upload → U-Net inference → mask / overlay / count pipeline
- [x] Fallback Otsu demo mode (works without GPU checkpoint)
- [x] Per-user job history and annotations

## B. Authentication (+base points)

- [x] JWT register / login / `/auth/me`
- [x] First registered user auto-promoted to admin
- [x] Password hashed with bcrypt
- [x] Identical error message for wrong email vs wrong password (prevents enumeration)
- [x] TOTP 2FA with pyotp (setup + verify-setup + 2-step login)
- [x] Scoped temp JWT for mid-login 2FA state (cannot access protected endpoints)
- [x] Email OTP — `send` + `verify` with 10-minute expiry, invalidated after use (+5 pts)
- [x] Google OAuth (+base)
- [x] GitHub OAuth (+5 pts)
- [x] Dropbox OAuth (+10 pts)

## C. Authorization (+10 pts)

- [x] `UserRole` enum: `admin` / `researcher` / `viewer`
- [x] `require_role()` dependency factory
- [x] Admin sees all jobs; others see own only
- [x] Admin endpoints: list users, change role, delete user, stats
- [x] Admin dashboard page in frontend (stats cards + user table + inline role editor)
- [x] `AdminRoute` component blocks non-admins client-side
- [x] Admin nav link only visible to admins

## C2. Account Management

- [x] `PATCH /auth/me` — update username and/or email (conflict detection, 409 on clash)
- [x] `POST /auth/change-password` — verify current password, hash and store new password
- [x] Profile page — avatar, edit form, password change form, 2FA status card
- [x] Toast notification system (success / error / info, auto-dismiss 4s)
- [x] Confirm modal (promise-based, replaces all `window.confirm()` calls)
- [x] All `alert()` / `confirm()` calls replaced across Dashboard, AdminPage, JobDetailPage

## D. Testing (+15 pts)

- [x] **85 pytest backend unit tests** across 6 suites (test_auth, test_crud, test_roles, test_totp, test_security, test_export, test_profile)
- [x] In-memory SQLite test engine with `StaticPool`
- [x] ML dependencies mocked at `sys.modules` level before any backend import
- [x] Rate limiting bypassed via `autouse` fixture patching `_check_request_limit`
- [x] **17 Playwright E2E tests** (auth flows, navigation, CRUD, admin panel)
- [x] **GitHub Actions CI/CD** — 4 jobs: backend-tests → frontend-typecheck → frontend-build → e2e-tests
- [x] Deploy jobs trigger on push to `main` only (after all tests pass)

## E. Deployment (+10 pts)

- [x] `Dockerfile` — Python 3.12 slim, no ML stack needed, ~250MB image
- [x] `fly.toml` — Fly.io config with persistent 1GB volume for file storage
- [x] `.dockerignore` — excludes data/, ML training scripts, checkpoints
- [x] Cloudflare Pages `_redirects` (SPA catch-all)
- [x] Cloudflare Pages `_headers` (security headers served by CDN)
- [x] `.env.production` with Fly.io backend URL
- [x] CI deploy jobs: `flyctl deploy` + `wrangler pages deploy` on main push

## F. Security

- [x] `SecurityHeadersMiddleware`: X-Content-Type-Options, X-Frame-Options, Referrer-Policy, Permissions-Policy, HSTS (prod), CSP
- [x] Magic-bytes image validation (8 signatures: PNG, JPEG, TIFF LE/BE, BMP, GIF)
- [x] `secrets.randbelow()` for OTP generation (not `random`)
- [x] Password strength validator (must have ≥1 letter and ≥1 digit)
- [x] Rate limits: register 10/min, login 5/min, email-otp 3/min, analyze 20/min
- [x] CORS locked to `FRONTEND_URL` only in production
- [x] API docs (`/docs`, `/redoc`) disabled in production
- [x] `/reset-db` route not registered in production
- [x] Path traversal guard uses `Path.resolve()` + prefix check
- [x] `pip-audit` in CI for known CVE scanning
- [x] TOTP code validated as exactly 6 digits (schema `pattern` field)
- [x] Email OTP invalidated after first use
- [x] Email OTP anti-enumeration (always returns same message regardless of email existence)

## G. README

- [x] Feature matrix with bonus point categories
- [x] Mermaid architecture diagram
- [x] Request flow walkthrough
- [x] Tech stack table
- [x] Local dev setup instructions
- [x] Database schema
- [x] Full API reference table
- [x] Authentication flow diagrams
- [x] Test suite summary
- [x] Deployment instructions (Fly.io + Cloudflare Pages)
- [x] Project structure tree
- [x] Environment variable reference

## H. Presentation

- [ ] Live demo script rehearsed (register → upload image → view result → 2FA setup → admin panel)
- [ ] 5-minute timing check
- [ ] Backup: recorded screen capture of full demo flow
- [ ] Slide deck covering: problem, architecture, auth flows, demo screenshots, test results, bonus summary

---

## Bonus Points Summary

| Bonus | Pts | Implemented |
|---|---|---|
| Email OTP (2nd 2FA method) | +5 | ✅ |
| GitHub OAuth | +5 | ✅ |
| Dropbox OAuth | +10 | ✅ |
| RBAC + Admin Dashboard | +10 | ✅ |
| pytest + Playwright + CI/CD | +15 | ✅ |
| Dockerfile + Fly.io deployment | +10 | ✅ |
| **Total** | **+55** | |

---

## Sign-off

| Member | Role | Sign-off date |
|---|---|---|
| M1 | Project Manager | _[YYYY-MM-DD]_ |
| M2 | Lead Developer | _[YYYY-MM-DD]_ |
| M3 | AI/ML Engineer | _[YYYY-MM-DD]_ |
| M4 | UX/UI Designer | _[YYYY-MM-DD]_ |
