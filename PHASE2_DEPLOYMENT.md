# Phase 2: Production Deployment Guide

## Overview
Deploy the Micro-Consent Pipeline to free hosting services for public testing and evaluation.

## Architecture
```
Internet
├── microconsent.dev (Vercel/Netlify)
│   └── Landing page with CTAs
├── dashboard.microconsent.dev (Streamlit Cloud)
│   └── Interactive analysis UI
└── api.microconsent.dev (Render/Railway)
    ├── FastAPI application
    ├── PostgreSQL database
    └── Redis cache
```

## Hosting Services

### 1. API Service (FastAPI)
**Options:**
- **Render** (recommended): `render.yaml` configuration
- **Railway**: CLI/web deployment

**Requirements:**
- Python 3.10+
- PostgreSQL database
- Redis cache
- Environment variables (API_KEY, DATABASE_URL, etc.)

### 2. Dashboard (Streamlit)
**Provider:** Streamlit Community Cloud
- Free tier: 1GB RAM, public apps
- Custom domain support
- Environment variables for API configuration

### 3. Database & Cache
**Provider:** Railway (free tier)
- PostgreSQL: 1GB storage
- Redis: 100MB storage
- Internal networking (no external access needed)

### 4. Landing Page
**Options:**
- **Vercel** (recommended): `vercel.json` configuration
- **Netlify**: `netlify.toml` configuration

**Tech Stack:** Vite + React + Tailwind CSS

## Deployment Steps

### Step 1: Environment Setup
1. Generate API key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
2. Set up Railway project with PostgreSQL + Redis
3. Configure environment variables (see ENVIRONMENT_VARIABLES.md)

### Step 2: API Deployment
Choose one:
- **Render**: Connect GitHub repo, use `render.yaml`
- **Railway**: Use CLI commands in RAILWAY_DEPLOYMENT.md

### Step 3: Dashboard Deployment
1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Connect GitHub repo
3. Set main file: `dashboard/app.py`
4. Configure environment variables
5. Add custom domain: `dashboard.microconsent.dev`

### Step 4: Landing Page Deployment
Choose one:
- **Vercel**: Connect repo, use `landing-page/vercel.json`
- **Netlify**: Connect repo, use `landing-page/netlify.toml`

### Step 5: DNS Configuration
Configure custom domains:
- `microconsent.dev` → Vercel/Netlify
- `dashboard.microconsent.dev` → Streamlit Cloud
- `api.microconsent.dev` → Render/Railway

### Step 6: Testing
Use E2E_TESTING_CHECKLIST.md to verify all components work together.

## URLs Summary
- **Landing Page:** https://microconsent.dev
- **Dashboard:** https://dashboard.microconsent.dev
- **API:** https://api.microconsent.dev
- **API Docs:** https://api.microconsent.dev/docs
- **Metrics:** https://api.microconsent.dev/metrics

## Free Tier Limits
- **Render:** 750 hours/month, 512MB RAM
- **Railway:** 512MB RAM, 1GB Postgres, 100MB Redis, 100 hours/month
- **Streamlit Cloud:** 1GB RAM, community support
- **Vercel:** 100GB bandwidth/month, hobby plan
- **Netlify:** 100GB bandwidth/month, personal plan

## Cost Optimization
- Monitor usage to stay within free tiers
- Implement caching to reduce database load
- Use CDN for static assets
- Consider paid upgrades if usage exceeds limits

## Next Steps
- Set up monitoring and alerting
- Implement user feedback collection
- Plan for scaling beyond free tiers
- Consider additional features (user accounts, API rate limiting, etc.)