# Docker Configuration

This directory contains Docker Compose configuration for ClinCode Copilot.

## Quick Start

From the project root:

```bash
docker compose -f docker/docker-compose.yml up -d
```

Or from this directory:

```bash
cd docker
docker compose up -d
```

## Files

- `docker-compose.yml` - Main Docker Compose configuration
- `DOCKER.md` - Comprehensive Docker documentation

## Access Points

- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs

## Documentation

For complete setup instructions, configuration options, and troubleshooting, see [DOCKER.md](DOCKER.md).
