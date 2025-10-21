# Deployment Guide

## Docker Deployment

### Local Development

#### 1. Build the Docker Image

```bash
docker build -t micro-consent-pipeline .
```

#### 2. Run the Container

```bash
# Run with port mapping
docker run -p 8000:8000 -p 8501:8501 micro-consent-pipeline

# Run with environment variables
docker run -p 8000:8000 -p 8501:8501 -e DEBUG=false -e LOG_LEVEL=WARNING micro-consent-pipeline

# Run in detached mode
docker run -d -p 8000:8000 -p 8501:8501 --name consent-pipeline micro-consent-pipeline
```

#### 3. Access Services

- **FastAPI**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Streamlit Dashboard**: http://localhost:8501

### Production Deployment

#### Docker Compose (Recommended)

Create `docker-compose.yml`:

```yaml
version: "3.8"
services:
  consent-pipeline:
    build: .
    ports:
      - "8000:8000"
      - "8501:8501"
    environment:
      - DEBUG=false
      - LOG_LEVEL=INFO
      - MIN_CONFIDENCE=0.7
    volumes:
      - ./outputs:/app/outputs
    restart: unless-stopped
```

Run with:

```bash
docker-compose up -d
```

#### Environment Configuration

Copy and modify the environment file:

```bash
cp .env.example .env
# Edit .env with your configuration
docker run --env-file .env -p 8000:8000 -p 8501:8501 micro-consent-pipeline
```

## CI/CD Pipeline

### GitHub Actions Workflow

The project includes automated CI/CD with GitHub Actions (`.github/workflows/ci.yml`):

#### Pipeline Stages:

1. **Test**: Run pytest on Python 3.10 and 3.11
2. **Docker Build**: Build and test Docker image
3. **Deploy**: Push to Docker Hub (main branch only)

#### Setting Up Secrets

For Docker Hub deployment, add these secrets to your GitHub repository:

1. Go to your GitHub repository
2. Click Settings → Secrets and variables → Actions
3. Add the following secrets:
   - `DOCKER_USERNAME`: Your Docker Hub username
   - `DOCKER_PASSWORD`: Your Docker Hub password or access token

### Manual CI/CD Commands

#### Local Testing

```bash
# Run tests
pytest -v

# Test Docker build
docker build -t micro-consent-pipeline-test .

# Test Docker run
docker run --rm micro-consent-pipeline-test python -c "from micro_consent_pipeline import PipelineRunner; print('Success')"
```

#### Docker Hub Deployment

```bash
# Tag for Docker Hub
docker tag micro-consent-pipeline your-username/micro-consent-pipeline:latest

# Push to Docker Hub
docker push your-username/micro-consent-pipeline:latest
```

## Cloud Platform Deployment

### Railway

```bash
# Install Railway CLI
npm install -g @railway/cli

# Login and deploy
railway login
railway init
railway up
```

### Render

1. Connect your GitHub repository to Render
2. Create a new Web Service
3. Set build command: `docker build -t app .`
4. Set start command: `docker run -p $PORT:8000 app`

### Heroku

Create `heroku.yml`:

```yaml
build:
  docker:
    web: Dockerfile
run:
  web: uvicorn api.app:app --host 0.0.0.0 --port $PORT
```

Deploy:

```bash
heroku create your-app-name
heroku stack:set container
git push heroku main
```

### DigitalOcean App Platform

1. Connect GitHub repository
2. Select Docker as the source
3. Set HTTP port to 8000
4. Deploy

## Monitoring and Logs

### Docker Logs

```bash
# View logs
docker logs consent-pipeline

# Follow logs
docker logs -f consent-pipeline

# View last 100 lines
docker logs --tail 100 consent-pipeline
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Test analysis endpoint
curl -X POST http://localhost:8000/analyze \
  -H "Content-Type: application/json" \
  -d '{"source": "<html><body><button>Accept</button></body></html>"}'
```

## Troubleshooting

### Common Issues

1. **Port already in use**

   ```bash
   # Find process using port
   lsof -i :8000
   # Kill process
   kill -9 <PID>
   ```

2. **Memory issues**

   ```bash
   # Increase Docker memory limit
   docker run -m 2g -p 8000:8000 -p 8501:8501 micro-consent-pipeline
   ```

3. **spaCy model not found**
   ```bash
   # Download model manually
   docker run --rm micro-consent-pipeline python -m spacy download en_core_web_sm
   ```

### Performance Optimization

1. **Multi-stage build** (for production):

   ```dockerfile
   FROM python:3.10-slim as builder
   # ... build dependencies

   FROM python:3.10-slim as production
   # ... copy only needed files
   ```

2. **Resource limits**:
   ```yaml
   # docker-compose.yml
   deploy:
     resources:
       limits:
         memory: 1G
         cpus: "0.5"
   ```

## Security Considerations

1. **Don't expose debug mode in production**
2. **Use environment variables for secrets**
3. **Regular security updates**:

   ```bash
   docker pull python:3.10-slim
   docker build --no-cache -t micro-consent-pipeline .
   ```

4. **Network security**:
   ```bash
   # Run with read-only filesystem
   docker run --read-only -p 8000:8000 -p 8501:8501 micro-consent-pipeline
   ```
