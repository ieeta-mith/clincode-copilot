# Docker Setup for ClinCode Copilot

This document explains how to run ClinCode Copilot using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+ and Docker Compose 2.0+
- Model files must be present in the `models/` directory at the project root
- At least 4GB RAM available for Docker

## Quick Start

All commands should be run from the project root directory.

```bash
# Build and start all services
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f

# Stop all services
docker compose -f docker/docker-compose.yml down
```

Alternatively, you can run commands from the `docker/` directory:
```bash
cd docker
docker compose up -d
```

The application will be available at:
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Project Structure

```
.
├── docker/
│   ├── docker-compose.yml     # Main compose configuration
│   └── DOCKER.md              # This documentation file
├── app/
│   └── Dockerfile             # Backend container definition
├── frontend/
│   └── Dockerfile             # Frontend container definition
├── models/                    # ML models (must exist, not in git)
│   ├── end_to_end/
│   ├── knn_chunks/
│   ├── ensemble/
│   └── icd_dictionary.json
└── icd_hybrid/                # ML core library
```

## Services

### Backend (FastAPI)

**Image**: Python 3.14
**Port**: 8000:80
**Health Check**: GET /health

Environment variables (all prefixed with `CLINCODE_`):
- `DEVICE`: cpu or cuda (default: cpu)
- `MODEL_DIR`: Path to models directory (default: /code/models)
- `ICD_DICTIONARY_PATH`: Path to ICD dictionary JSON
- `MAX_CHUNKS`: Maximum text chunks to process (default: 20)
- `MAX_LENGTH`: Maximum tokens per chunk (default: 128)
- `CHUNK_OVERLAP`: Token overlap between chunks (default: 32)
- `NEIGHBOR_COUNT`: Number of similar patients to return (default: 50)
- `CORS_ORIGINS`: Allowed CORS origins as JSON array

**Volume**: `../models` (relative to docker/) is mounted read-only to `/code/models`

### Frontend (Next.js)

**Image**: Node 20 Alpine (multi-stage build)
**Port**: 3000:3000
**Health Check**: wget http://localhost:3000

Build args:
- `NEXT_PUBLIC_API_URL`: API URL for build-time embedding (default: http://localhost:8000)

Runtime environment:
- `NEXT_PUBLIC_API_URL`: API URL for client-side requests (default: http://backend:80)

The frontend uses Next.js standalone output mode for optimized production builds.

## Models Directory

The `models/` directory is **required** and must contain:

```
models/
├── end_to_end/
│   ├── end_to_end.pt          # PyTorch model checkpoint
│   └── config.json
├── knn_chunks/
│   ├── faiss_index.bin        # FAISS index file
│   └── config.json
├── ensemble/
│   ├── ensemble_config.json   # Weights and thresholds
│   └── label_encoder.json
└── icd_dictionary.json        # ICD-9 code descriptions
```

If models are missing, the backend will start but return 503 errors.

## Configuration

### Using Environment Variables

Create a `.env` file in the `docker/` directory or project root:

```env
# Backend configuration
CLINCODE_DEVICE=cpu
CLINCODE_MAX_CHUNKS=20
CLINCODE_CORS_ORIGINS=["http://localhost:3000","http://localhost:3001"]

# Frontend configuration
NEXT_PUBLIC_API_URL=http://localhost:8000
```

Then run from project root:
```bash
docker compose -f docker/docker-compose.yml --env-file .env up -d
```

Or from docker/ directory:
```bash
cd docker
docker compose --env-file ../.env up -d
```

### GPU Support

To enable GPU acceleration:

1. Install [NVIDIA Container Toolkit](https://docs.nvidia.com/datacenter/cloud-native/container-toolkit/install-guide.html)

2. Update `docker/docker-compose.yml`:
```yaml
services:
  backend:
    environment:
      - CLINCODE_DEVICE=cuda
    deploy:
      resources:
        reservations:
          devices:
            - driver: nvidia
              count: 1
              capabilities: [gpu]
```

3. Rebuild and restart:
```bash
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d --build
```

## Development vs Production

### Development Mode

For local development with hot-reload, run services natively:

```bash
# Terminal 1 - Backend
pip install -r requirements.txt
uvicorn app.main:app --reload

# Terminal 2 - Frontend
cd frontend
npm install
npm run dev
```

### Production Mode

Use Docker Compose for production deployments:

```bash
docker compose -f docker/docker-compose.yml up -d
```

## Common Commands

All commands assume you're running from the project root. Add `-f docker/docker-compose.yml` to each command, or `cd docker` first.

```bash
# Build images without starting
docker compose -f docker/docker-compose.yml build

# Rebuild specific service
docker compose -f docker/docker-compose.yml build backend
docker compose -f docker/docker-compose.yml build frontend

# Start services
docker compose -f docker/docker-compose.yml up -d

# View logs
docker compose -f docker/docker-compose.yml logs -f backend
docker compose -f docker/docker-compose.yml logs -f frontend

# Execute command in running container
docker compose -f docker/docker-compose.yml exec backend bash
docker compose -f docker/docker-compose.yml exec frontend sh

# Stop services
docker compose -f docker/docker-compose.yml stop

# Stop and remove containers
docker compose -f docker/docker-compose.yml down

# Stop and remove containers + volumes
docker compose -f docker/docker-compose.yml down -v

# View service status
docker compose -f docker/docker-compose.yml ps

# View resource usage
docker stats
```

## Troubleshooting

### Backend fails with "Models not loaded"

- Ensure `models/` directory exists at project root
- Check that all required model files are present
- Verify volume mount in docker-compose.yml
- Check backend logs: `docker compose -f docker/docker-compose.yml logs backend`

### Frontend cannot connect to backend

- Verify `NEXT_PUBLIC_API_URL` environment variable
- Check that backend is healthy: `docker compose -f docker/docker-compose.yml ps`
- Ensure services are on same Docker network
- Check frontend logs: `docker compose -f docker/docker-compose.yml logs frontend`

### Build fails with dependency errors

- Clear Docker build cache: `docker compose -f docker/docker-compose.yml build --no-cache`
- Update base images: `docker compose -f docker/docker-compose.yml pull`
- Check that package-lock.json is in sync: `cd frontend && npm ci`

### Memory issues

- Increase Docker memory limit in Docker Desktop settings
- Reduce `CLINCODE_MAX_CHUNKS` to process fewer chunks
- Use smaller batch sizes if processing multiple requests

### Port already in use

If ports 3000 or 8000 are already bound:

```yaml
# In docker/docker-compose.yml, change port mappings:
services:
  backend:
    ports:
      - "8001:80"  # Changed from 8000
  frontend:
    ports:
      - "3001:3000"  # Changed from 3000
    environment:
      - NEXT_PUBLIC_API_URL=http://backend:80
```

## Health Checks

Both services implement health checks:

```bash
# Check backend health
curl http://localhost:8000/health

# Check frontend health
curl http://localhost:3000

# View health status in Docker
docker compose -f docker/docker-compose.yml ps
```

Healthy services show "healthy" status. The frontend depends on backend health before starting.

## Security Notes

- Models volume is mounted read-only (`:ro`)
- Frontend runs as non-root user (nextjs:nodejs)
- No sensitive data in environment variables by default
- CORS is configured to allow only specified origins
- Health check endpoints are publicly accessible

## Updating the Application

```bash
# Pull latest code
git pull

# Rebuild and restart services
docker compose -f docker/docker-compose.yml down
docker compose -f docker/docker-compose.yml up -d --build

# Or rebuild specific service
docker compose -f docker/docker-compose.yml up -d --build backend
```

## Clean Up

```bash
# Remove all containers and networks
docker compose -f docker/docker-compose.yml down

# Remove containers, networks, and images
docker compose -f docker/docker-compose.yml down --rmi all

# Remove everything including volumes
docker compose -f docker/docker-compose.yml down -v --rmi all
```
