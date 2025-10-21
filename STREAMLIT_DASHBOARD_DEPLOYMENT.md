# Streamlit Dashboard Deployment Guide

## Prerequisites

- GitHub repository with dashboard code
- Deployed Micro-Consent API (Render/Railway)
- Streamlit Cloud account

## Step-by-Step Deployment

### 1. Prepare Repository

Ensure your repository has:

```
dashboard/
├── app.py
├── requirements.txt
├── streamlit_app.toml
└── README.md
```

### 2. Access Streamlit Cloud

1. Visit [share.streamlit.io](https://share.streamlit.io)
2. Sign in with GitHub
3. Click **"New app"**

### 3. Configure App Settings

```
Repository: MitPete/Micro-Consent-Pipeline
Branch: main
Main file path: dashboard/app.py
App URL: dashboard.microconsent.dev (optional custom domain)
```

### 4. Set Environment Variables

Add these secrets in the app settings:

| Variable   | Value                          | Description                       |
| ---------- | ------------------------------ | --------------------------------- |
| `API_BASE` | `https://api.microconsent.dev` | Your deployed API endpoint        |
| `API_KEY`  | `your-api-key`                 | (Optional) API authentication key |

### 5. Deploy

- Click **"Deploy!"**
- Wait for build completion
- Access your live dashboard

## Custom Domain (Optional)

1. In Streamlit app settings → "Settings" → "Domain"
2. Add `dashboard.microconsent.dev`
3. Configure DNS CNAME to Streamlit's provided target

## Testing Deployment

### Health Check

```bash
# Test API connectivity
curl -X POST https://api.microconsent.dev/health
# Should return: {"status":"ok","version":"1.0.0"}
```

### Dashboard Test

1. Open `https://dashboard.microconsent.dev`
2. Enter test HTML: `<button>Accept Cookies</button>`
3. Click "Analyze"
4. Verify results appear
5. Check browser network tab for API calls

### Common Issues

- **CORS errors**: Ensure API allows dashboard domain in ALLOWED_ORIGINS
- **API connection failed**: Check API_BASE URL and API_KEY
- **Timeout errors**: API might be processing heavy content
- **No results**: Try different HTML or lower confidence threshold

## Free Tier Limits

- 1GB RAM per app
- Community support
- Public apps only
- No private repositories

## Advanced Configuration

### Custom Theme

Edit `streamlit_app.toml`:

```toml
[theme]
base="dark"
primaryColor="#ff4b4b"
backgroundColor="#0e1117"
secondaryBackgroundColor="#262730"
```

### Performance Optimization

- Use `st.cache_data` for expensive operations
- Implement pagination for large result sets
- Add loading states for better UX

## Monitoring

- Check Streamlit Cloud logs for errors
- Monitor API usage via Render/Railway dashboards
- Set up alerts for failed deployments
