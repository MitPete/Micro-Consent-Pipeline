# End-to-End Testing Checklist

## Pre-Deployment Setup
- [ ] Generate secure API key: `python -c "import secrets; print(secrets.token_urlsafe(32))"`
- [ ] Set up Railway project and add PostgreSQL + Redis plugins
- [ ] Deploy API to Render or Railway with environment variables
- [ ] Deploy dashboard to Streamlit Cloud with API_BASE set
- [ ] Deploy landing page to Vercel/Netlify with custom domain

## API Testing
- [ ] Health check: `curl https://api.microconsent.dev/health`
  - Expected: `{"status":"ok","version":"1.0.0"}`
- [ ] API docs accessible: `https://api.microconsent.dev/docs`
- [ ] CORS headers allow dashboard domain
- [ ] Authentication required for `/analyze` endpoint

## Dashboard Testing
- [ ] Streamlit app loads: `https://dashboard.microconsent.dev`
- [ ] Can input HTML content for analysis
- [ ] API calls succeed (check browser network tab)
- [ ] Results display correctly
- [ ] Error handling works for invalid inputs

## Landing Page Testing
- [ ] Site loads: `https://microconsent.dev`
- [ ] CTA buttons link to correct URLs:
  - "Try the Live Dashboard" → `https://dashboard.microconsent.dev`
  - GitHub link → repository
- [ ] API docs section shows correct endpoints
- [ ] Responsive design works on mobile/desktop
- [ ] All links functional

## Integration Testing
- [ ] Full workflow: Landing page → Dashboard → API analysis
- [ ] Database persistence: Results stored and retrievable
- [ ] Async processing: Long analyses don't block UI
- [ ] Error scenarios: Invalid API key, malformed HTML, network issues

## Performance Testing
- [ ] API response time < 2 seconds for typical consent analysis
- [ ] Dashboard loads within 5 seconds
- [ ] Landing page loads within 3 seconds
- [ ] Concurrent users handled (test with multiple browser tabs)

## Monitoring Verification
- [ ] Prometheus metrics endpoint: `https://api.microconsent.dev/metrics`
- [ ] Logs accessible in hosting platform
- [ ] Error tracking configured
- [ ] Grafana dashboard placeholder visible (if implemented)

## Security Testing
- [ ] HTTPS enabled on all domains
- [ ] API key authentication working
- [ ] CORS properly configured
- [ ] No sensitive data in client-side code
- [ ] Rate limiting functional (if implemented)

## Post-Launch Tasks
- [ ] Update DNS records for custom domains
- [ ] Configure monitoring alerts
- [ ] Set up backup procedures
- [ ] Document incident response process
- [ ] Announce launch on social media/GitHub