# NucleiAI — Cell Nuclei Analysis Platform

A full-stack web application for automated cell nuclei detection and segmentation in microscopy images. Researchers upload histology images and receive instant segmentation masks, overlays, cell counts, PDF reports, and community-sharing tools.

---

## Table of Contents

- [Features](#features)
- [Tech Stack](#tech-stack)
- [Project Structure](#project-structure)
- [Getting Started (Local Development)](#getting-started-local-development)
- [Environment Variables](#environment-variables)
- [Role System](#role-system)
- [API Overview](#api-overview)
- [Deployment Guide](#deployment-guide)
- [Security Notes](#security-notes)

---

## Features

### Core Analysis
- Upload microscopy images (JPEG, PNG, TIFF, BMP) up to 20 MB
- U-Net deep learning model for cell nuclei segmentation
- Returns original image, binary mask, and color overlay
- Estimated cell count with processing time and metadata
- Falls back to demo mode if model is unavailable

### Dashboard
- View all personal analysis jobs
- Search and filter by filename, job ID, or mode
- Paginated job table with stats (total cells, avg cells/job)
- 7-day trend chart of cells counted
- Export all jobs to CSV
- Delete jobs

### Job Detail
- Full image viewer (original, mask, overlay)
- Processing metadata (device, threshold, min area, image size)
- Research annotations — add, view, and delete notes per job
- Download PDF report

### Explore (Community)
- Publish analyses publicly with a headline and description
- Browse all community publications in a card grid
- Filter by mode, cell count range, or search by author/title
- Open modal with full image set, stats, comments
- Save publications to favourites
- Download PDF report of any published analysis
- View any user's public profile and publications

### Authentication
- Email + password login with strength enforcement
- Email OTP login (passwordless)
- Google, GitHub, and Dropbox OAuth
- Two-factor authentication (TOTP / authenticator app)
- Forgot password flow with 6-digit code via email
- Server-side token revocation on logout

### Admin Panel
- Manager role: create admin accounts, manage all users
- Admin role: manage viewers and researchers
- Promote / demote users between viewer and researcher
- Delete users (cascades all their records)
- Site-wide stats (total users, jobs, cells by role)

### Notifications
- Bell icon with unread count badge in sidebar
- Notified when someone favourites or comments on your publication
- Mark all as read on open

---

## Tech Stack

| Layer | Technology |
|---|---|
| Frontend | React 18, TypeScript, Vite, React Router |
| Backend | FastAPI, Python 3.12, SQLModel, Uvicorn |
| Database | SQLite (dev) / PostgreSQL (production) |
| ML Model | PyTorch, U-Net (segmentation-models-pytorch) |
| Auth | JWT (python-jose), bcrypt (passlib), TOTP (pyotp) |
| OAuth | Authlib (Google, GitHub, Dropbox) |
| Rate Limiting | slowapi |
| PDF Generation | ReportLab |
| Email | SMTP (Gmail App Password) |

---

## Project Structure

```
nuclei-ai/
├── web-programming/
│   ├── backend/
│   │   ├── main.py              # All API routes
│   │   ├── models.py            # SQLModel ORM tables
│   │   ├── schemas.py           # Pydantic request/response DTOs
│   │   ├── auth_utils.py        # JWT, password hashing, OTP, email
│   │   ├── dependencies.py      # FastAPI auth dependencies
│   │   ├── crud.py              # Database operations
│   │   ├── database.py          # Engine and session setup
│   │   ├── config.py            # Environment variable loading
│   │   ├── security.py          # Security headers middleware
│   │   ├── oauth.py             # OAuth provider registration
│   │   ├── totp_utils.py        # TOTP/2FA helpers
│   │   ├── seed.py              # First manager account bootstrap
│   │   ├── requirements.txt
│   │   ├── .env.example         # Template — copy to .env
│   │   ├── storage/
│   │   │   ├── uploads/         # Raw uploaded images (gitignored)
│   │   │   └── results/         # Masks and overlays (gitignored)
│   │   └── services/
│   │       └── analysis_service.py  # ML model wrapper
│   └── frontend/
│       ├── src/
│       │   ├── api.ts           # All API calls
│       │   ├── App.tsx          # Routes
│       │   ├── styles.css       # Global dark theme styles
│       │   ├── components/      # Reusable UI components
│       │   └── pages/           # Page components
│       ├── .env.development
│       └── .env.production
```

---

## Getting Started (Local Development)

### Prerequisites

- Python 3.11 or 3.12
- Node.js 18+
- Git

### 1. Clone the repository

```bash
git clone https://github.com/3bada66/nuclei-ai.git
cd nuclei-ai/web-programming
```

### 2. Backend setup

```bash
cd backend

# Create virtual environment
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux

# Install dependencies
pip install -r requirements.txt

# Copy and fill in environment variables
copy .env.example .env       # Windows
# cp .env.example .env       # macOS/Linux
# Edit .env with your values (see Environment Variables section)

# Create the first manager account (run once)
python -m backend.seed

# Start the backend
cd ..
uvicorn backend.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend setup

```bash
cd frontend

# Install dependencies
npm install

# Start the dev server
npm run dev
```

The app is now running at:
- **Frontend:** http://localhost:5173
- **Backend API:** http://127.0.0.1:8000
- **API Docs:** http://127.0.0.1:8000/docs (development only)

---

## Environment Variables

Copy `backend/.env.example` to `backend/.env` and fill in the values:

```env
# Required
SECRET_KEY=            # Generate with: python -c "import secrets; print(secrets.token_hex(64))"
DATABASE_URL=          # sqlite:///./nuclei.db  (dev)  or  postgresql://user:pass@host/db  (prod)
ENV=                   # development | staging | production
FRONTEND_URL=          # http://localhost:5173 (dev) or https://yourdomain.com (prod)

# Email OTP and password reset (Gmail App Password)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your.email@gmail.com
SMTP_PASSWORD=         # 16-char Gmail App Password
EMAIL_FROM=your.email@gmail.com

# Google OAuth (optional)
GOOGLE_CLIENT_ID=
GOOGLE_CLIENT_SECRET=

# GitHub OAuth (optional)
GITHUB_CLIENT_ID=
GITHUB_CLIENT_SECRET=

# Dropbox OAuth (optional)
DROPBOX_CLIENT_ID=
DROPBOX_CLIENT_SECRET=
```

> **Never commit `.env` to git.** It is already in `.gitignore`.

---

## Role System

| Role | Description | Can access admin panel |
|---|---|---|
| `manager` | Full privileges. Created only via `seed.py`. | Yes |
| `admin` | Can manage viewers and researchers. Created by manager. | Yes |
| `researcher` | Can run analyses, publish, comment. | No |
| `viewer` | Same as researcher (self-selectable). | No |

### Role rules
- Manager cannot be created from the UI — only via `python -m backend.seed`
- Admin cannot promote users to admin or manager
- Admin cannot delete or modify other admins or the manager
- Viewers and researchers can switch between those two roles themselves

---

## API Overview

All protected endpoints require `Authorization: Bearer <token>`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/auth/register` | Create account |
| `POST` | `/auth/login` | Login with email/password |
| `POST` | `/auth/logout` | Revoke token server-side |
| `POST` | `/auth/forgot-password` | Send reset code to email |
| `POST` | `/auth/verify-reset-code` | Verify 6-digit code |
| `POST` | `/auth/reset-password` | Set new password with token |
| `POST` | `/auth/email-otp/send` | Send OTP to email |
| `POST` | `/auth/email-otp/verify` | Verify OTP and get token |
| `POST` | `/auth/2fa/setup` | Generate TOTP secret |
| `POST` | `/auth/2fa/verify` | Complete 2FA login |
| `GET` | `/auth/google` | Start Google OAuth flow |
| `GET` | `/auth/github` | Start GitHub OAuth flow |
| `GET` | `/auth/dropbox` | Start Dropbox OAuth flow |
| `POST` | `/api/analyze` | Upload and analyze an image |
| `GET` | `/api/jobs` | List jobs (own or all for admin) |
| `GET` | `/api/jobs/{id}` | Get job detail with annotations |
| `DELETE` | `/api/jobs/{id}` | Delete a job |
| `GET` | `/api/jobs/{id}/report.pdf` | Download PDF report |
| `POST` | `/api/jobs/{id}/publish` | Publish to Explore |
| `GET` | `/api/explore` | List all publications |
| `GET` | `/api/favourites` | List favourited publications |
| `GET` | `/api/notifications` | List notifications |
| `GET` | `/api/health` | Health check (DB + model) |
| `GET` | `/admin/users` | List users (admin/manager) |
| `PATCH` | `/admin/users/{id}/role` | Change user role |
| `DELETE` | `/admin/users/{id}` | Delete user |

---

## Deployment Guide

### Prerequisites
- A PostgreSQL database (Railway, Supabase, Neon, etc.)
- An object storage bucket for images (Cloudflare R2, AWS S3, etc.)
- A domain or free subdomain from your hosting platform

### Steps

**1. Set environment variables on your server:**
```env
ENV=production
SECRET_KEY=<64+ char random string>
DATABASE_URL=postgresql://user:pass@host:5432/dbname
FRONTEND_URL=https://yourdomain.com
```

**2. Update OAuth redirect URIs** in each provider's dashboard:
```
https://yourdomain.com/auth/google/callback
https://yourdomain.com/auth/github/callback
https://yourdomain.com/auth/dropbox/callback
```

**3. Seed the database** (run once on a fresh DB):
```bash
python -m backend.seed
```

**4. Build the frontend:**
```bash
cd frontend
npm run build
# Deploy the dist/ folder to Vercel, Netlify, or Cloudflare Pages
```

**5. Start the backend:**
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --workers 2
```

**6. Put a reverse proxy (nginx/Caddy) in front** to handle HTTPS and serve static files.

### Recommended free hosting

| Service | Purpose | Free tier |
|---|---|---|
| Vercel | Frontend (React) | Yes — unlimited |
| Railway | Backend (FastAPI) + PostgreSQL | $5/month credit |
| Cloudflare R2 | Image storage | 10 GB free |

---

## Security Notes

- Passwords require: 8+ characters, uppercase, lowercase, digit, and special character
- Passwords are hashed with bcrypt (never stored in plaintext)
- JWTs are revoked server-side on logout (stored in DB until expiry)
- Rate limiting on all sensitive endpoints (login, 2FA, OTP, register)
- All file uploads validated by magic bytes (not just Content-Type header)
- File serving protected against path traversal attacks
- OAuth tokens exchanged via short-lived server-side codes (never in URLs)
- HTML escaped in all PDF output to prevent ReportLab injection
- Security headers on every response: HSTS, X-Frame-Options, CSP, etc.
- API docs disabled in staging and production (`ENV=development` only)
- `.env` is gitignored — secrets are never committed

---

## License

MIT
