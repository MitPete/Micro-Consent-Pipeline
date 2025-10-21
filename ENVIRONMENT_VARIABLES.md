# Environment Variables Template

## API Service (Render/Railway)

```bash
# Required
API_KEY=your-secure-api-key-here
ALLOWED_ORIGINS=https://dashboard.microconsent.dev,https://microconsent.dev
DATABASE_URL=postgresql://user:password@host:5432/dbname
REDIS_URL=redis://host:6379/0

# Optional
ENVIRONMENT=production
LOG_LEVEL=INFO
MAX_PAYLOAD_BYTES=10485760
REQUEST_TIMEOUT=30
```

## Dashboard (Streamlit Cloud)

```bash
API_BASE=https://api.microconsent.dev
ENVIRONMENT=production
```

## Landing Page (Vercel/Netlify)

No environment variables required - all links are hardcoded.

## Security Notes

- Generate a strong API_KEY using: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- Never commit API keys to version control
- Use service-specific secret management (Render secrets, Railway variables, Streamlit secrets)
