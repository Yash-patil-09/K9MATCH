# 🚀 K9Match Production Deployment Guide

This guide provides step-by-step instructions for deploying the **K9Match** platform to production cloud environments (Render, Railway, or VPS) with managed PostgreSQL, WhiteNoise static compression, and Cloudinary persistent media storage.

---

## 🏗️ Production Architecture Overview

| Component | Service / Technology | Description |
|---|---|---|
| **Web Server (WSGI)** | **Gunicorn** (`gunicorn config.wsgi:application`) | Multi-worker Python HTTP server. |
| **Static Assets** | **WhiteNoise** (`CompressedManifestStaticFilesStorage`) | Serves hashed, Brotli/Gzip-compressed CSS/JS directly with far-future caching. |
| **Media & Images** | **Cloudinary** (`django-cloudinary-storage`) | Stores uploaded dog profile pictures and pedigree cards persistently. |
| **Database** | **PostgreSQL** (Render Postgres, Supabase, or Neon) | Production relational database via `dj-database-url`. |
| **Email Service** | **Gmail SMTP** or SendGrid | Sends transactional match emails and password resets. |
| **Vet Discovery API**| **Google Maps Places API (New)** | Live geolocation, autocomplete, and veterinary lookups. |

---

## 📋 Pre-Deployment Checklist

Before deploying, ensure you have:
1. A Git repository hosted on **GitHub** or **GitLab**.
2. An account on your cloud hosting platform (e.g. [Render.com](https://render.com), [Railway.app](https://railway.app)).
3. A free account on [Cloudinary.com](https://cloudinary.com) for persistent image hosting.
4. Google Cloud Console credentials for Google OAuth and Google Maps Places API.

---

## 🌐 Option 1: Deploying to Render (Recommended)

Render offers a streamlined deployment path using the included [`render.yaml`](file:///d:/K9Match/render.yaml) blueprint or manual Web Service setup.

### Step 1: Push Code to GitHub
Ensure all recent changes are committed and pushed to your GitHub repository:
```bash
git add .
git commit -m "Configure Phase 4 production deployment"
git push origin master
```

### Step 2: Create a Blueprint or Web Service on Render
1. Log in to [Render Dashboard](https://dashboard.render.com/).
2. Click **New +** -> **Blueprint**.
3. Connect your GitHub repository (`K9Match`).
4. Render will detect [`render.yaml`](file:///d:/K9Match/render.yaml) and automatically configure:
   - A managed PostgreSQL database (`k9match-db`).
   - A Python web service (`k9match-web`) with `./build.sh` build command and Gunicorn start command.

### Step 3: Configure Environment Variables
In the Render Web Service settings, navigate to **Environment** and populate the following keys:

```env
DEBUG=False
SECRET_KEY=<your-random-generated-production-secret-key>
ALLOWED_HOSTS=.onrender.com,yourcustomdomain.com
SECURE_SSL_REDIRECT=True
SESSION_COOKIE_SECURE=True
CSRF_COOKIE_SECURE=True

# Cloudinary Storage (Required so uploaded dog images persist across deploys)
CLOUDINARY_CLOUD_NAME=your_cloud_name
CLOUDINARY_API_KEY=your_api_key
CLOUDINARY_API_SECRET=your_api_secret

# Email Notifications (Gmail App Password)
EMAIL_HOST_USER=your-email@gmail.com
EMAIL_HOST_PASSWORD=your-16-character-app-password

# Google OAuth2 Authentication
GOOGLE_CLIENT_ID=your_client_id.apps.googleusercontent.com
GOOGLE_CLIENT_SECRET=your_client_secret

# Google Maps / Places API
GOOGLE_MAPS_API_KEY=your_google_maps_api_key
```

*Note: The `DATABASE_URL` is automatically linked from `k9match-db` when using the blueprint.*

### Step 4: Initial Build & Verification
Render will trigger `./build.sh`:
1. `pip install -r requirements.txt`
2. `python manage.py collectstatic --no-input`
3. `python manage.py migrate`

Once deployed, click your `.onrender.com` URL to verify the home page, explore search, and login flows.

---

## 🗄️ Database Migration: SQLite to PostgreSQL

If you have existing test or seed data in `db.sqlite3` that you want to move to your live PostgreSQL database:

### 1. Export Data from SQLite (Local Machine)
Run the custom K9Match export command:
```powershell
python manage.py export_db_data --output datadump.json
```
*(This automatically exports all dog profiles, reviews, and users while cleanly excluding content types to prevent primary key conflicts).*

### 2. Import into Production PostgreSQL
In your cloud shell (or locally pointing `DATABASE_URL` to your production database):
```bash
# Apply initial table migrations
python manage.py migrate

# Load your exported records
python manage.py loaddata datadump.json

# Seed veterinary clinics if needed
python manage.py seed_vets
```

---

## 🖼️ Setting Up Cloudinary Media Storage

Local cloud containers (Render, Railway, Heroku) feature **ephemeral filesystems** — files uploaded to local disk are wiped whenever the server restarts or deploys new code.

To ensure uploaded dog photos and certificates persist permanently:
1. Sign up for a free account at [Cloudinary.com](https://cloudinary.com/).
2. On your Cloudinary Dashboard, copy:
   - **Cloud Name**
   - **API Key**
   - **API Secret**
3. Set these three values in your cloud host's Environment Variables:
   - `CLOUDINARY_CLOUD_NAME`
   - `CLOUDINARY_API_KEY`
   - `CLOUDINARY_API_SECRET`
4. K9Match automatically detects these variables in `config/settings.py` and routes all image uploads to Cloudinary with secure HTTPS delivery.

---

## 🔑 Google Cloud Production Whitelist

To enable Google Sign-In on your production domain:
1. Open [Google Cloud Console](https://console.cloud.google.com/) -> **APIs & Services** -> **Credentials**.
2. Edit your **OAuth 2.0 Client ID**.
3. Under **Authorized JavaScript origins**, add:
   - `https://your-service.onrender.com` (and your custom domain)
4. Under **Authorized redirect URIs**, add:
   - `https://your-service.onrender.com/accounts/google/login/callback/`
   - `https://your-service.onrender.com/google/callback/`
5. Save changes.

---

## 🔒 Custom Domain & SSL Configuration

1. In Render Dashboard, go to your Web Service -> **Settings** -> **Custom Domains**.
2. Add your domain (e.g., `k9match.com` or `app.k9match.com`).
3. Add the provided `CNAME` or `A` records to your DNS provider (Cloudflare, GoDaddy, Namecheap).
4. Render automatically provisions and renews a free Let's Encrypt SSL certificate.
5. In your Environment Variables, update `ALLOWED_HOSTS`:
   ```env
   ALLOWED_HOSTS=.onrender.com,k9match.com,www.k9match.com
   ```
