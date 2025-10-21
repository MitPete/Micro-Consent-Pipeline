# API and Dashboard Usage Guide

## FastAPI REST API

### Starting the API Server

```bash
# Option 1: Direct (with required security configuration)
export API_KEY=your-secure-api-key-here
export ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501
python api/app.py

# Option 2: Using startup script
./scripts/start_api.sh

# Option 3: Using uvicorn directly
uvicorn api.app:app --host 0.0.0.0 --port 8000 --reload
```

The API will be available at: http://localhost:8000

### Security Configuration

**⚠️ Required: Set API Key**

```bash
# Generate a secure API key
export API_KEY=$(python -c "import secrets; print(secrets.token_urlsafe(32))")

# Or set a custom key
export API_KEY=your-secure-api-key-here
```

**CORS Configuration**

```bash
# Allow specific origins (production)
export ALLOWED_ORIGINS=https://your-app.com,https://dashboard.your-app.com

# Allow localhost (development)
export ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501
```

**Optional Security Settings**

```bash
export MAX_PAYLOAD_BYTES=10485760  # 10MB max payload
export REQUEST_TIMEOUT=30          # 30 second timeout
```

### API Documentation

- Interactive docs: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc
- Metrics: http://localhost:8000/metrics (Prometheus)

### API Endpoints

#### Health Check (No Authentication Required)

```bash
curl http://localhost:8000/health
```

Response:

```json
{
  "status": "ok",
  "timestamp": "2023-12-07T10:30:00.123456",
  "version": "0.1.0"
}
```

#### Analyze Consent Content (Authentication Required)

**With X-API-Key Header (Recommended):**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "source": "<html><body><button>Accept All</button></body></html>",
    "output_format": "json"
  }'
```

**With Authorization Header:**

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer your-api-key-here" \
  -d '{
    "source": "https://example.com/privacy-policy",
    "output_format": "json"
  }'
```

**Response:**

```json
{
  "success": true,
  "items": [
    {
      "text": "Accept All",
      "category": "Functional",
      "confidence": 0.8,
      "type": "button",
      "element": "button"
    }
  ],
  "total_items": 1,
  "categories": {
    "Functional": 1
  },
  "request_id": "abc12345"
}
```

### Input Validation

#### Supported URL Schemes

- ✅ `https://example.com/privacy`
- ✅ `http://localhost:8080/privacy`
- ❌ `file:///etc/passwd` (blocked for security)
- ❌ `ftp://example.com/file` (blocked for security)

#### Content Limits

- Maximum payload: 10MB (configurable)
- HTML content is automatically sanitized
- Request timeout: 30 seconds

#### Output Formats

- `json` (default)
- `csv`

### Rate Limiting

**Current Limits:**

- Health endpoint: 60 requests/minute per IP
- Analyze endpoint: 10 requests/minute per IP

**Rate Limit Response (429):**

```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "request_id": "abc12345",
  "retry_after": 60
}
```

### Error Responses

#### Authentication Error (401)

```json
{
  "detail": "API key required. Provide key in X-API-Key header or Authorization: Bearer <key>"
}
```

#### Validation Error (422)

```json
{
  "detail": [
    {
      "loc": ["body", "source"],
      "msg": "Only HTTP and HTTPS URLs are allowed",
      "type": "value_error"
    }
  ]
}
```

#### Payload Too Large (413)

```json
{
  "detail": "Payload too large. Maximum allowed: 10485760 bytes"
}
```

#### Request Timeout (408)

```json
{
  "detail": {
    "error": "Request timeout after 30 seconds",
    "request_id": "abc12345"
  }
}
```

```json
{
  "success": true,
  "items": [
    {
      "text": "Accept All",
      "category": "Functional",
      "confidence": 0.8,
      "type": "button",
      "element": "button"
    }
  ],
  "total_items": 1,
  "categories": {
    "Functional": 1
  }
}
```

## Streamlit Dashboard

### Starting the Dashboard

```bash
# Option 1: Direct
streamlit run dashboard/app.py

# Option 2: Using startup script
./scripts/start_dashboard.sh
```

The dashboard will be available at: http://localhost:8501

### Dashboard Features

- **Input Methods**: Text input, file upload, or URL
- **Interactive Analysis**: Real-time consent analysis
- **Visualizations**: Category distribution charts
- **Configuration**: Adjustable confidence thresholds
- **Results Export**: View detailed JSON results

### Usage

1. Choose your input method (Text, File, or URL)
2. Configure settings in the sidebar
3. Click "Analyze" to process the content
4. View results in tables and charts
5. Expand "Detailed Results" for JSON output

## Integration Examples

### Python Client

```python
import requests

# Configure API settings
API_BASE_URL = "http://localhost:8000"
API_KEY = "your-api-key-here"

# Headers with authentication
headers = {
    "Content-Type": "application/json",
    "X-API-Key": API_KEY
}

# Analyze HTML content
def analyze_html(html_content):
    response = requests.post(
        f"{API_BASE_URL}/analyze",
        headers=headers,
        json={
            "source": html_content,
            "output_format": "json"
        }
    )

    if response.status_code == 200:
        return response.json()
    elif response.status_code == 401:
        print("Authentication failed - check API key")
    elif response.status_code == 429:
        print("Rate limit exceeded - wait before retrying")
    else:
        print(f"Error: {response.status_code} - {response.text}")

    return None

# Analyze URL
def analyze_url(url):
    response = requests.post(
        f"{API_BASE_URL}/analyze",
        headers=headers,
        json={
            "source": url,
            "output_format": "json"
        }
    )

    return response.json() if response.status_code == 200 else None

# Example usage
html = "<html><body><button>Accept Cookies</button></body></html>"
result = analyze_html(html)

if result:
    print(f"Found {result['total_items']} consent items")
    print(f"Request ID: {result['request_id']}")
    for item in result['items']:
        print(f"- {item['text']}: {item['category']} ({item['confidence']:.2f})")
```

### JavaScript Client

```javascript
class ConsentAnalyzer {
  constructor(apiKey, baseUrl = "http://localhost:8000") {
    this.apiKey = apiKey;
    this.baseUrl = baseUrl;
  }

  async analyzeContent(source, outputFormat = "json") {
    try {
      const response = await fetch(`${this.baseUrl}/analyze`, {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "X-API-Key": this.apiKey,
        },
        body: JSON.stringify({
          source: source,
          output_format: outputFormat,
        }),
      });

      if (!response.ok) {
        if (response.status === 401) {
          throw new Error("Authentication failed - check API key");
        } else if (response.status === 429) {
          throw new Error("Rate limit exceeded - please wait");
        } else {
          throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
      }

      return await response.json();
    } catch (error) {
      console.error("Analysis failed:", error);
      throw error;
    }
  }

  async checkHealth() {
    const response = await fetch(`${this.baseUrl}/health`);
    return response.json();
  }
}

// Example usage
const analyzer = new ConsentAnalyzer("your-api-key-here");

analyzer
  .analyzeContent("<button>Accept All Cookies</button>")
  .then((result) => {
    console.log(`Found ${result.total_items} consent items`);
    console.log(`Request ID: ${result.request_id}`);
    result.items.forEach((item) => {
      console.log(
        `- ${item.text}: ${item.category} (${item.confidence.toFixed(2)})`
      );
    });
  })
  .catch((error) => {
    console.error("Error:", error.message);
  });
```

### cURL Examples

#### Basic Analysis

```bash
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key-here" \
  -d '{
    "source": "https://example.com/privacy-policy",
    "output_format": "json"
  }'
```

#### With Error Handling

```bash
#!/bin/bash
API_KEY="your-api-key-here"
API_URL="http://localhost:8000"

response=$(curl -s -w "%{http_code}" -X POST "$API_URL/analyze" \
  -H "Content-Type: application/json" \
  -H "X-API-Key: $API_KEY" \
  -d '{
    "source": "https://example.com/privacy",
    "output_format": "json"
  }')

http_code="${response: -3}"
body="${response%???}"

case $http_code in
  200)
    echo "Success: $body"
    ;;
  401)
    echo "Authentication failed - check API key"
    ;;
  422)
    echo "Validation error: $body"
    ;;
  429)
    echo "Rate limit exceeded - wait 60 seconds"
    ;;
  *)
    echo "Error $http_code: $body"
    ;;
esac
```

## Production Deployment

### Docker (Recommended)

```dockerfile
FROM python:3.10-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

# API
EXPOSE 8000
CMD ["uvicorn", "api.app:app", "--host", "0.0.0.0", "--port", "8000"]

# Dashboard (separate container)
# EXPOSE 8501
# CMD ["streamlit", "run", "dashboard/app.py", "--server.port", "8501", "--server.address", "0.0.0.0"]
```

### Environment Variables

```bash
# Required Security Settings
export API_KEY=your-secure-production-api-key
export ALLOWED_ORIGINS=https://your-app.com,https://dashboard.your-app.com

# Optional Configuration
export FASTAPI_PORT=8000
export STREAMLIT_PORT=8501
export LOG_LEVEL=INFO
export MIN_CONFIDENCE=0.5
export MAX_PAYLOAD_BYTES=10485760
export REQUEST_TIMEOUT=30
```

### Docker Compose with Security

```yaml
version: "3.8"
services:
  api:
    build: .
    ports:
      - "8000:8000"
    environment:
      - API_KEY=${API_KEY}
      - ALLOWED_ORIGINS=${ALLOWED_ORIGINS}
      - LOG_LEVEL=INFO
      - MAX_PAYLOAD_BYTES=10485760
      - REQUEST_TIMEOUT=30
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

### Security Best Practices

1. **Never expose API keys in code**
2. **Use environment variables for configuration**
3. **Set restrictive CORS origins in production**
4. **Monitor rate limiting and authentication logs**
5. **Use HTTPS in production**
6. **Implement proper error handling in clients**
7. **Rotate API keys regularly**

### Load Testing

```bash
# Install Apache Bench
sudo apt-get install apache2-utils

# Test with authentication
ab -n 100 -c 10 -H "X-API-Key: your-api-key" \
   -p analyze_request.json -T application/json \
   http://localhost:8000/analyze
```

Where `analyze_request.json` contains:

```json
{
  "source": "https://example.com/privacy",
  "output_format": "json"
}
```
