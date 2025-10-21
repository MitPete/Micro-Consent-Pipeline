# Streamlit Cloud Deployment Guide

## Prerequisites

- GitHub repository connected to Streamlit Cloud
- API deployed and accessible (e.g., https://api.microconsent.dev)

## Deployment Steps

### 1. Access Streamlit Cloud

1. Go to [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub account
3. Click "New app"

### 2. Configure App

```
Repository: MitPete/Micro-Consent-Pipeline
Branch: main
Main file path: dashboard/app.py
App URL: dashboard.microconsent.dev
```

### 3. Set Environment Variables

```
API_BASE=https://api.microconsent.dev
ENVIRONMENT=production
```

### 4. Advanced Settings

- Python version: 3.10
- Requirements file: requirements.txt
- Secrets: Add API_KEY if needed for internal calls

### 5. Deploy

Click "Deploy!" button

## Custom Domain Setup

1. In Streamlit Cloud app settings
2. Add custom domain: `dashboard.microconsent.dev`
3. Configure DNS CNAME record pointing to Streamlit's servers

## Verification

- Visit `https://dashboard.microconsent.dev`
- Test consent analysis with sample HTML
- Verify API calls work (check browser network tab)

## Free Tier Limits

- 1GB RAM per app
- Community support only
- Public apps only (no private)
