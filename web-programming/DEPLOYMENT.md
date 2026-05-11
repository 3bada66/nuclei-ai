# NucleiAI — Deployment Guide

Full step-by-step instructions to deploy the backend to Fly.io and the frontend to Cloudflare Pages, and wire up automatic CI/CD via GitHub Actions.

---

## Prerequisites

- A [Fly.io](https://fly.io) account (free tier works)
- A [Cloudflare](https://cloudflare.com) account (free tier works)
- [flyctl](https://fly.io/docs/hands-on/install-flyctl/) installed on your machine
- Python 3.11+ installed locally (for generating the secret key)

---

## Part 1 — Backend on Fly.io

### Step 1: Login to Fly.io

```bash
flyctl auth login
```

### Step 2: Create the app (first time only)

```bash
cd web-programming/
flyctl launch --no-deploy --name nuclei-ai-backend
```

When prompted, say **No** to creating a Postgres database — you will do it in the next step.

### Step 3: Create a Postgres database and attach it

```bash
flyctl postgres create --name nuclei-ai-db
flyctl postgres attach nuclei-ai-db --app nuclei-ai-backend
```

This automatically sets `DATABASE_URL` as a secret on the app.

### Step 4: Create a persistent volume for uploaded images

```bash
flyctl volumes create nuclei_storage --size 1 --region iad --app nuclei-ai-backend
```

### Step 5: Set all application secrets

Run this block exactly as-is — it sets every required secret in one command:

```bash
flyctl secrets set \
  SECRET_KEY="$(python -c 'import secrets; print(secrets.token_hex(64))')" \
  ENV="production" \
  FRONTEND_URL="https://nuclei-ai-frontend.pages.dev" \
  SMTP_HOST="smtp.gmail.com" \
  SMTP_PORT="587" \
  SMTP_USER="your-gmail@gmail.com" \
  SMTP_PASSWORD="your-16-char-gmail-app-password" \
  GOOGLE_CLIENT_ID="your-google-client-id" \
  GOOGLE_CLIENT_SECRET="your-google-client-secret" \
  GITHUB_CLIENT_ID="your-github-client-id" \
  GITHUB_CLIENT_SECRET="your-github-client-secret" \
  --app nuclei-ai-backend
```

> **Where to find these values:** They are in the `.env` file on the developer's machine (`web-programming/backend/.env`). Copy them from there — never paste real secrets into any file that gets committed to git.

> **Note:** `SECRET_KEY` is generated fresh each time — never reuse the dev key.

### Step 6: Deploy the backend

```bash
flyctl deploy --app nuclei-ai-backend
```

This builds the Docker image remotely and deploys it. First deploy takes 3–5 minutes.

### Step 7: Create the first manager account

```bash
flyctl ssh console --app nuclei-ai-backend
```

Inside the container shell:

```bash
python -m backend.seed
# Follow the prompts: enter username, email, and a strong password
exit
```

### Step 8: Get the backend URL

```bash
flyctl status --app nuclei-ai-backend
```

The URL will look like `https://nuclei-ai-backend.fly.dev` — **save this**, you need it for Cloudflare and OAuth.

### Step 9: Get the Fly.io API token for CI

```bash
flyctl auth token
```

Copy the token — you will add it to GitHub in Part 3.

---

## Part 2 — Frontend on Cloudflare Pages

### Step 1: Go to the Cloudflare dashboard

[dash.cloudflare.com](https://dash.cloudflare.com) → **Pages → Create a project → Connect to Git**

### Step 2: Connect your GitHub repo

- Repository: `3bada66/nuclei-ai`
- Production branch: `main`
- Build command: `cd web-programming/frontend && npm ci && npm run build`
- Build output directory: `web-programming/frontend/dist`
- Root directory: leave as `/`

### Step 3: Add environment variable in Cloudflare

In the Pages project settings → **Environment variables → Production**:

| Variable | Value |
|---|---|
| `VITE_API_URL` | `https://nuclei-ai-backend.fly.dev` |

Replace the URL with the actual URL from Part 1 Step 8.

### Step 4: Get your Cloudflare tokens

**API Token:**
Cloudflare dashboard → **My Profile → API Tokens → Create Token** → use the **Edit Cloudflare Workers** template → copy the token.

**Account ID:**
Visible in the right sidebar of the Cloudflare dashboard home page.

---

## Part 3 — Add secrets to GitHub for auto-deploy

Go to: `github.com/3bada66/nuclei-ai` → **Settings → Secrets and variables → Actions → New repository secret**

Add all of these:

| Secret name | Value |
|---|---|
| `FLY_API_TOKEN` | Token from Part 1 Step 9 |
| `CLOUDFLARE_API_TOKEN` | Token from Part 2 Step 4 |
| `CLOUDFLARE_ACCOUNT_ID` | Account ID from Part 2 Step 4 |
| `VITE_API_URL` | `https://nuclei-ai-backend.fly.dev` |

---

## Part 4 — Enable auto-deploy in the CI workflow

Open `.github/workflows/test.yml` and find these two lines:

```yaml
if: false  # Enable when FLY_API_TOKEN secret is added to GitHub → Settings → Secrets
```

```yaml
if: false  # Enable when CLOUDFLARE_API_TOKEN + CLOUDFLARE_ACCOUNT_ID secrets are added
```

Change **both** to:

```yaml
if: github.ref == 'refs/heads/main' && github.event_name == 'push'
```

Commit and push — from now on every merge to `main` automatically deploys both backend and frontend.

---

## Part 5 — Update OAuth redirect URLs

After the backend is live, add the production callback URLs in each provider's dashboard.

### Google

[console.cloud.google.com](https://console.cloud.google.com) → APIs & Services → Credentials → your OAuth client → **Authorized redirect URIs** → Add:

```
https://nuclei-ai-backend.fly.dev/auth/google/callback
```

### GitHub

[github.com/settings/developers](https://github.com/settings/developers) → OAuth Apps → your app → **Authorization callback URL** → Add:

```
https://nuclei-ai-backend.fly.dev/auth/github/callback
```

### Dropbox

[dropbox.com/developers/apps](https://www.dropbox.com/developers/apps) → your app → **Redirect URIs** → Add:

```
https://nuclei-ai-backend.fly.dev/auth/dropbox/callback
```

---

## Troubleshooting

**Backend not starting:**
```bash
flyctl logs --app nuclei-ai-backend
```

**Database connection error:**
```bash
flyctl postgres connect --app nuclei-ai-db
```

**Re-run the seed script:**
```bash
flyctl ssh console --app nuclei-ai-backend -C "python -m backend.seed"
```

**Check app status:**
```bash
flyctl status --app nuclei-ai-backend
```
