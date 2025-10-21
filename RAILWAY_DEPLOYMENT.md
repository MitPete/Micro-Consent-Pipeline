# Railway Deployment Guide

## Database & Redis Setup

### 1. Create Railway Project

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login
railway login

# Create new project
railway init micro-consent-pipeline
```

### 2. Add PostgreSQL Database

```bash
# Add PostgreSQL plugin
railway add postgres

# Get connection string
railway variables get DATABASE_URL
```

### 3. Add Redis Cache

```bash
# Add Redis plugin
railway add redis

# Get connection string
railway variables get REDIS_URL
```

### 4. Set Environment Variables

```bash
# Set required environment variables
railway variables set API_KEY=your-secure-api-key-here
railway variables set ALLOWED_ORIGINS=https://dashboard.microconsent.dev,https://microconsent.dev
railway variables set ENVIRONMENT=production
railway variables set LOG_LEVEL=INFO
```

### 5. Deploy API Service

```bash
# Connect to GitHub repo
railway connect github

# Deploy
railway up
```

### 6. Get Service URL

```bash
railway domain
# Should return: https://micro-consent-pipeline.railway.app
```

## Expected URLs

- API: `https://micro-consent-pipeline.railway.app` (or custom domain)
- Database: Internal Railway connection
- Redis: Internal Railway connection

## Free Tier Limits

- 512MB RAM
- 1GB storage (PostgreSQL)
- 100MB storage (Redis)
- 100 hours/month runtime
