# Live Demo Script

**Time budget:** ~4 minutes  
**Prereqs:** backend running on :8000, frontend on :5173, browser open at `/login`

---

## 0 — Setup (before presenting)

```sh
# Terminal A
cd web-programming
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload

# Terminal B
cd web-programming/frontend
npm run dev
```

Open `http://localhost:5173` in a clean browser profile (no stored token).

---

## 1 — Register + auto-login  (30 s)

1. Go to `/register`
2. Fill in username `demo`, email `demo@nuclei.ai`, password `Demo1234`
3. Click **Create account** → redirected to `/dashboard`

**Say:** *"First user is automatically admin — no manual DB setup needed."*

---

## 2 — Analyze an image  (45 s)

1. Click **Analyze** in the sidebar
2. Drop any PNG/JPG histopathology image (or use one from `data/processed/images/`)
3. Click **Analyze** button
4. Wait ~2 s → result appears: cell count, input / mask / overlay images

**Say:** *"In production this runs the U-Net model. In demo mode it uses Otsu thresholding — same UI, same API contract."*

---

## 3 — Job history + annotation  (30 s)

1. Click **Dashboard** → the job just appears in the list
2. Click the job row → detail page with three image panels
3. Type a note in the annotation box → click **Save**

---

## 4 — TOTP 2FA  (45 s)

1. Click **Security** in the sidebar → `/2fa/setup`
2. QR code appears — scan with Google Authenticator (or show URI)
3. Enter the 6-digit code → 2FA enabled confirmation

4. Click **Sign out** → `/login`
5. Log in with `demo@nuclei.ai` / `Demo1234`
6. Response is `requires_2fa: true` → redirected to `/2fa/verify`
7. Enter the code → full access token → dashboard

**Say:** *"Temp token has scope='2fa' and cannot access any other endpoint — shown in test_security.py."*

---

## 5 — Register a second user + admin panel  (45 s)

1. Open a **second browser tab** (or incognito)
2. Register `viewer1` / `viewer@nuclei.ai` / `Viewer123`
3. This user is `viewer` role — no Admin link in sidebar

4. Back to the **first tab** (admin) → click **Admin**
5. Show the stats row: Total Users = 2, Total Jobs = 1
6. Show the user table — change `viewer1`'s role to `researcher` via the dropdown
7. Switch back to viewer tab → refresh → badge updates

---

## 6 — Tests (30 s — show in terminal)

```sh
cd web-programming
python -m pytest backend/tests/ -q
```

```
65 passed in ~30s
```

**Say:** *"Includes magic-bytes upload validation, TOTP scope enforcement, security headers, and password strength — all regression-tested."*

---

## 7 — CI badge (15 s)

Show `.github/workflows/test.yml` — 4 jobs, deploy only on `main` push.

**Say:** *"Deploy to Fly.io and Cloudflare Pages happens automatically after all 65 unit tests and 17 E2E tests pass."*

---

## Fallback: if live demo breaks

- Show the test run output (saved beforehand)
- Open Swagger UI at `http://127.0.0.1:8000/docs` and demo the endpoints directly
- Show screenshots of the admin dashboard saved in `docs/screenshots/` (create these ahead of time)

---

## Key talking points

| Feature | Proof to show |
|---|---|
| JWT + TOTP 2FA | Live login flow (steps 4–5) |
| Email OTP | `[DEV EMAIL OTP] → demo@nuclei.ai  code: 123456` in terminal |
| GitHub/Discord OAuth | Buttons visible on `/login` (grayed out if env vars not set — explain) |
| RBAC | Viewer has no Admin link; admin can change roles live |
| Magic-bytes security | Try uploading a `.txt` renamed to `.png` → 400 error |
| 65 tests | `pytest -q` in terminal |
| Deployment | Show `fly.toml` and `Dockerfile` |
