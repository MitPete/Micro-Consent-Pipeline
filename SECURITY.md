# Security Guide

This document outlines the security measures implemented in the Micro-Consent-Pipeline project and provides best practices for secure deployment and operation.

## Overview

The Micro-Consent-Pipeline implements defense-in-depth security measures including:

- **API Key Authentication**: Protect endpoints from unauthorized access
- **Rate Limiting**: Prevent abuse and DoS attacks
- **Input Validation**: Prevent injection attacks and malformed data
- **CORS Controls**: Restrict cross-origin requests to approved domains
- **Security Headers**: Implement browser security controls
- **Audit Logging**: Comprehensive security event logging
- **Request Timeouts**: Prevent resource exhaustion attacks

## Threat Model

### Identified Threats

1. **Unauthorized API Access**

   - **Risk**: Attackers accessing the /analyze endpoint without permission
   - **Mitigation**: API key authentication required for protected endpoints

2. **Server-Side Request Forgery (SSRF)**

   - **Risk**: Attackers providing internal URLs to access restricted resources
   - **Mitigation**: URL validation restricting to HTTP/HTTPS only, no file:// schemes

3. **Denial of Service (DoS)**

   - **Risk**: Resource exhaustion through high-volume requests or large payloads
   - **Mitigation**: Rate limiting, payload size limits, request timeouts

4. **Cross-Site Scripting (XSS)**

   - **Risk**: Malicious scripts in HTML content affecting dashboard users
   - **Mitigation**: HTML sanitization using bleach, security headers

5. **Cross-Origin Resource Sharing (CORS) Abuse**

   - **Risk**: Unauthorized cross-origin requests from malicious websites
   - **Mitigation**: Strict CORS origin allowlist

6. **Data Injection Attacks**
   - **Risk**: Malformed or malicious input causing system compromise
   - **Mitigation**: Comprehensive input validation, Pydantic models

## Security Configuration

### Environment Variables

Configure the following security-related environment variables:

```bash
# API Authentication
API_KEY=your-secure-api-key-here

# CORS Configuration
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501,https://your-domain.com

# Request Limits
MAX_PAYLOAD_BYTES=10485760  # 10MB maximum request size
REQUEST_TIMEOUT=30          # 30 seconds maximum request duration

# General Security
LOG_LEVEL=INFO              # Enable security audit logging
```

### Required Security Settings

#### 1. API Key Management

**Generate Strong API Keys:**

```bash
# Generate a secure API key (32+ characters)
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

**API Key Best Practices:**

- Use keys with 32+ characters
- Include uppercase, lowercase, numbers, and special characters
- Rotate keys regularly (quarterly recommended)
- Store keys securely (environment variables, secret managers)
- Never commit keys to version control
- Use different keys for different environments

#### 2. CORS Origin Configuration

**Production Setup:**

```bash
# Only allow specific trusted domains
ALLOWED_ORIGINS=https://your-app.com,https://dashboard.your-app.com
```

**Development Setup:**

```bash
# Allow localhost for development
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501,http://127.0.0.1:3000
```

#### 3. Rate Limiting Configuration

**Current Limits:**

- Global: 60 requests per minute per IP
- `/analyze` endpoint: 10 requests per minute per IP
- `/health` endpoint: 60 requests per minute per IP

**Customization:**
Modify limits in `api/app.py`:

```python
@limiter.limit("30/minute")  # Reduce to 30/min
@limiter.limit("5/minute")   # Reduce analyze to 5/min
```

#### 4. Payload and Timeout Limits

**Default Limits:**

- Maximum payload: 10MB
- Request timeout: 30 seconds

**Adjustment Guidelines:**

- Increase payload limit for large documents (max 50MB recommended)
- Increase timeout for complex processing (max 120 seconds recommended)

## API Security

### Authentication

All protected endpoints require API key authentication:

#### Header Method (Recommended):

```bash
curl -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"source": "https://example.com/privacy"}' \
     https://your-api.com/analyze
```

#### Authorization Header Method:

```bash
curl -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"source": "https://example.com/privacy"}' \
     https://your-api.com/analyze
```

### Protected Endpoints

- `POST /analyze` - **Requires API key**
- `GET /health` - **Open access** (for monitoring)
- `GET /metrics` - **Open access** (for monitoring)

### Rate Limiting

Rate limits are enforced per IP address:

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "request_id": "abc12345",
  "retry_after": 60
}
```

### Input Validation

#### URL Validation

- Only `http://` and `https://` schemes allowed
- No `file://`, `ftp://`, or other dangerous schemes
- Must match valid URL pattern

#### HTML Content Validation

- Maximum size: 1MB (configurable)
- Sanitized using bleach library
- Dangerous tags and attributes removed

#### Output Format Validation

- Only `json` and `csv` formats accepted
- Case-sensitive validation

## Security Headers

All responses include security headers:

```http
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
Referrer-Policy: no-referrer
Content-Security-Policy: default-src 'self'
X-XSS-Protection: 1; mode=block
X-Request-ID: abc12345
```

### Header Explanations

- **X-Content-Type-Options**: Prevents MIME type sniffing attacks
- **X-Frame-Options**: Prevents clickjacking by blocking iframe embedding
- **Referrer-Policy**: Prevents information leakage via referrer headers
- **Content-Security-Policy**: Restricts resource loading to same origin
- **X-XSS-Protection**: Enables browser XSS filtering
- **X-Request-ID**: Unique identifier for request tracing

## Audit Logging

### Security Events Logged

All security-relevant events are logged in structured JSON format:

#### Authentication Events

```json
{
  "timestamp": "2023-12-07T10:30:00.123Z",
  "level": "WARNING",
  "message": "Invalid API key",
  "request_id": "abc12345",
  "client_ip": "192.168.1.100",
  "user_agent": "curl/7.68.0",
  "auth_status": "invalid_key"
}
```

#### Rate Limiting Events

```json
{
  "timestamp": "2023-12-07T10:30:00.123Z",
  "level": "WARNING",
  "message": "Rate limit exceeded",
  "request_id": "abc12345",
  "client_ip": "192.168.1.100",
  "rate_limit_status": "exceeded",
  "endpoint": "/analyze"
}
```

#### Request Processing Events

```json
{
  "timestamp": "2023-12-07T10:30:00.123Z",
  "level": "INFO",
  "message": "Request completed",
  "request_id": "abc12345",
  "client_ip": "192.168.1.100",
  "status_code": 200,
  "duration_ms": 1500,
  "auth_status": "success"
}
```

### Log Analysis

Use structured logs for security monitoring:

```bash
# Find failed authentication attempts
grep '"auth_status": "invalid_key"' app.log

# Find rate limit violations
grep '"rate_limit_status": "exceeded"' app.log

# Find requests from specific IP
grep '"client_ip": "192.168.1.100"' app.log

# Find slow requests (potential DoS)
grep '"duration_ms": [0-9][0-9][0-9][0-9]' app.log
```

## Deployment Security

### Production Checklist

#### Before Deployment:

- [ ] Generate strong API key (32+ characters)
- [ ] Configure ALLOWED_ORIGINS for production domains only
- [ ] Set appropriate payload and timeout limits
- [ ] Enable structured logging (LOG_LEVEL=INFO or DEBUG)
- [ ] Configure log aggregation and monitoring
- [ ] Set up alerting for security events

#### Infrastructure Security:

- [ ] Use HTTPS/TLS for all communications
- [ ] Configure reverse proxy (nginx, Cloudflare) with additional security
- [ ] Implement network-level firewalls
- [ ] Use container security scanning
- [ ] Regular security updates for base images
- [ ] Implement backup and disaster recovery

#### Monitoring Setup:

- [ ] Monitor authentication failures
- [ ] Monitor rate limit violations
- [ ] Monitor unusual traffic patterns
- [ ] Set up alerts for error rate spikes
- [ ] Implement log retention policies

### Docker Security

#### Secure Container Configuration:

```yaml
services:
  micro-consent-pipeline:
    build: .
    environment:
      - API_KEY=${API_KEY} # Load from secure environment
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
    security_opt:
      - no-new-privileges:true
    read_only: true
    tmpfs:
      - /tmp:noexec,nosuid,size=100m
    user: "1000:1000" # Run as non-root user
```

#### Network Security:

```yaml
networks:
  app-network:
    driver: bridge
    internal: true # Prevent external access

services:
  micro-consent-pipeline:
    networks:
      - app-network
    ports:
      - "127.0.0.1:8000:8000" # Bind to localhost only
```

### Reverse Proxy Security

#### Nginx Configuration:

```nginx
server {
    listen 443 ssl http2;
    server_name your-api.com;

    # SSL configuration
    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    # Security headers
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    add_header X-Content-Type-Options nosniff always;
    add_header X-Frame-Options DENY always;

    # Rate limiting
    limit_req_zone $binary_remote_addr zone=api:10m rate=10r/m;
    limit_req zone=api burst=5 nodelay;

    # Payload size limit
    client_max_body_size 10M;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;

        # Security timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
}
```

## Incident Response

### Security Event Response

#### Authentication Failures:

1. **Investigate**: Check logs for pattern/source
2. **Block**: Consider IP blocking for persistent attacks
3. **Rotate**: Rotate API keys if compromise suspected
4. **Monitor**: Increase monitoring for related activity

#### Rate Limit Violations:

1. **Assess**: Determine if legitimate traffic spike or attack
2. **Scale**: Increase rate limits if legitimate traffic
3. **Block**: Implement additional blocking for attacks
4. **Review**: Analyze traffic patterns for optimization

#### Input Validation Failures:

1. **Analyze**: Review failed inputs for attack patterns
2. **Enhance**: Strengthen validation rules if needed
3. **Alert**: Notify security team of potential exploit attempts
4. **Patch**: Apply fixes for any discovered vulnerabilities

### Emergency Procedures

#### API Key Compromise:

```bash
# 1. Generate new API key
NEW_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# 2. Update environment configuration
echo "API_KEY=$NEW_KEY" >> .env

# 3. Restart application
docker-compose restart micro-consent-pipeline

# 4. Update client configurations
# Notify all API clients of new key
```

#### Service Under Attack:

```bash
# 1. Enable emergency rate limiting
# Update nginx configuration with stricter limits

# 2. Block attacking IPs at firewall level
iptables -A INPUT -s ATTACKING_IP -j DROP

# 3. Scale infrastructure if needed
# Add more application instances

# 4. Contact CDN/WAF provider for additional protection
```

## Security Testing

### Automated Security Tests

Run the security test suite:

```bash
# Run security-specific tests
pytest micro_consent_pipeline/tests/test_security.py -v

# Run all tests including security
pytest micro_consent_pipeline/tests/ -v

# Run with coverage
pytest micro_consent_pipeline/tests/test_security.py --cov=api
```

### Manual Security Testing

#### Authentication Testing:

```bash
# Test without API key (should fail)
curl -X POST https://your-api.com/analyze \
     -H "Content-Type: application/json" \
     -d '{"source": "https://example.com"}'

# Test with invalid API key (should fail)
curl -X POST https://your-api.com/analyze \
     -H "X-API-Key: invalid-key" \
     -H "Content-Type: application/json" \
     -d '{"source": "https://example.com"}'
```

#### Rate Limiting Testing:

```bash
# Test rate limits (should eventually return 429)
for i in {1..15}; do
  curl -X POST https://your-api.com/analyze \
       -H "X-API-Key: your-api-key" \
       -H "Content-Type: application/json" \
       -d '{"source": "https://example.com"}'
done
```

#### Input Validation Testing:

```bash
# Test dangerous URLs (should be rejected)
curl -X POST https://your-api.com/analyze \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"source": "file:///etc/passwd"}'

# Test oversized payload (should be rejected)
curl -X POST https://your-api.com/analyze \
     -H "X-API-Key: your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"source": "'$(python -c 'print("x" * 20000000)')'"}'
```

## Compliance and Standards

### Security Standards Compliance

- **OWASP Top 10**: Addresses injection, authentication, and security misconfiguration
- **NIST Cybersecurity Framework**: Implements identify, protect, detect, respond, recover
- **ISO 27001**: Follows information security management best practices

### Privacy Considerations

- **Data Minimization**: Only processes necessary data for analysis
- **Data Retention**: No long-term storage of processed content
- **Access Logging**: Comprehensive audit trail of all data access
- **Encryption**: HTTPS/TLS for data in transit

### Regular Security Reviews

#### Monthly Reviews:

- [ ] Review authentication failure logs
- [ ] Analyze rate limiting patterns
- [ ] Check for new security vulnerabilities
- [ ] Update dependencies with security patches

#### Quarterly Reviews:

- [ ] Rotate API keys
- [ ] Review and update rate limits
- [ ] Penetration testing
- [ ] Security configuration audit

#### Annual Reviews:

- [ ] Comprehensive security assessment
- [ ] Update threat model
- [ ] Review and update security documentation
- [ ] Security training for development team

## Support and Contact

For security-related issues:

- **Security Email**: security@your-domain.com
- **Emergency**: emergency-security@your-domain.com
- **Bug Reports**: Use GitHub security advisory for vulnerabilities

### Responsible Disclosure

We welcome security researchers to report vulnerabilities responsibly:

1. Email security@your-domain.com with details
2. Allow 90 days for resolution before public disclosure
3. Provide technical details and proof of concept
4. We will acknowledge receipt within 48 hours
