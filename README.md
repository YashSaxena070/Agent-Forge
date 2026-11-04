# AgentForge

AI-Powered Software Development Platform

## Overview

AgentForge is a comprehensive platform that uses AI agents to automate the software development lifecycle. It combines LangGraph workflow orchestration, specialized AI agents, Hybrid RAG, and production-ready infrastructure to take a product idea from concept to deployed application.

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        AgentForge Platform                       │
├─────────────────────────────────────────────────────────────────┤
│  Frontend (Next.js)          │  Backend (FastAPI)               │
│  ──────────────────────      │  ──────────────────              │
│  • Dashboard                 │  • REST API                      │
│  • Workflow Visualization    │  • Authentication/Authorization  │
│  • Agent Monitoring          │  • Workflow Orchestration        │
│  • Deployment Management     │  • Agent Management              │
│  • Observability             │  • RAG Pipeline                  │
└──────────────────────────────┴──────────────────────────────────┘
                              │
        ┌─────────────────────┼─────────────────────┐
        ▼                     ▼                     ▼
┌───────────────┐    ┌───────────────┐    ┌───────────────┐
│  LangGraph    │    │  Hybrid RAG   │    │   Memory      │
│  Orchestration│    │  (Qdrant+     │    │   Layer       │
│               │    │   Neo4j)      │    │               │
│ • StateGraph  │    │               │    │ • Redis       │
│ • Nodes/Edges │    │ • Vector Search│   │ • PostgreSQL  │
│ • Checkpoints │    │ • Graph Query │    │ • Qdrant      │
│ • Human-in-loop│   │ • Reranking   │    │ • Neo4j       │
└───────────────┘    └───────────────┘    └───────────────┘
        │                     │                     │
        └─────────────────────┼─────────────────────┘
                              ▼
                    ┌───────────────────┐
                    │  Infrastructure   │
                    │                   │
                    │ • PostgreSQL      │
                    │ • Redis           │
                    │ • Qdrant          │
                    │ • Neo4j           │
                    │ • Kafka           │
                    │ • Temporal        │
                    │ • MinIO           │
                    │ • Prometheus      │
                    │ • Grafana         │
                    │ • Loki/Tempo      │
                    └───────────────────┘
```

## Features

### Core Capabilities
- **Multi-Agent System**: 10 specialized agents (Planner, Product Manager, Architect, Backend, Frontend, Database, QA, Security, DevOps, Reviewer)
- **Workflow Orchestration**: LangGraph-based stateful workflows with checkpoints, retries, and human-in-the-loop approvals
- **Hybrid RAG**: Combined vector (Qdrant) and graph (Neo4j) retrieval with reranking
- **Memory Layer**: Short-term (Redis), long-term (PostgreSQL), semantic (Qdrant), and relationship (Neo4j) memory
- **MCP Integration**: GitHub, Docker, Kubernetes, Filesystem, Browser, Issue Tracker, Documentation
- **Durable Execution**: Temporal for long-running workflows with retries and recovery

### Production Features
- **Containerized**: Docker images for all services
- **Kubernetes Ready**: Deployments, HPA, Ingress, RBAC
- **CI/CD**: GitHub Actions with linting, testing, security scanning, and deployment
- **Observability**: OpenTelemetry, Prometheus, Grafana, Loki, Tempo
- **Security**: JWT auth, RBAC, rate limiting, audit logging

## Quick Start

### Prerequisites
- Docker & Docker Compose
- Python 3.11+
- Node.js 20+
- kubectl (for Kubernetes deployment)

### Local Development

1. **Clone and configure**
```bash
git clone https://github.com/yourorg/agentforge.git
cd agentforge
cp .env.example .env
# Edit .env with your API keys
```

2. **Start infrastructure**
```bash
docker-compose up -d postgres redis qdrant neo4j kafka temporal minio
```

3. **Start backend**
```bash
cd apps/backend
pip install -e ".[dev]"
alembic upgrade head
uvicorn src.main:app --reload
```

4. **Start frontend**
```bash
cd apps/frontend
npm install
npm run dev
```

5. **Access**
- Frontend: http://localhost:3000
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Temporal UI: http://localhost:8080
- Grafana: http://localhost:3001 (admin/admin)

### Production Deployment

```bash
# Build images
docker build -t agentforge/backend:v1.0.0 -f infra/docker/Dockerfile.backend .
docker build -t agentforge/frontend:v1.0.0 -f infra/docker/Dockerfile.frontend .
docker build -t agentforge/worker:v1.0.0 -f infra/docker/Dockerfile.worker .

# Deploy to Kubernetes
kubectl apply -k infra/kubernetes/overlays/production
```

## Project Structure

```
agentforge/
├── apps/
│   ├── backend/           # FastAPI backend
│   │   ├── src/
│   │   │   ├── api/       # REST endpoints
│   │   │   ├── agents/    # Specialized agents
│   │   │   ├── orchestration/  # LangGraph workflow
│   │   │   ├── rag/       # Hybrid RAG pipeline
│   │   │   ├── memory/    # Memory management
│   │   │   ├── integrations/  # MCP integrations
│   │   │   └── workers/   # Temporal/Kafka workers
│   │   └── tests/
│   └── frontend/          # Next.js dashboard
├── services/
│   └── shared/            # Shared libraries
├── agents/                # Agent implementations
├── orchestration/         # LangGraph components
├── rag/                   # RAG pipeline
├── memory/                # Memory systems
├── integrations/          # MCP & external integrations
├── infra/
│   ├── docker/            # Dockerfiles
│   ├── kubernetes/        # K8s manifests
│   └── terraform/         # Cloud infrastructure
├── monitoring/            # Prometheus, Grafana, Loki, Tempo
├── deployments/           # Helm, ArgoCD
├── docs/                  # Documentation
└── tests/                 # Integration & E2E tests
```

## Specialized Agents

| Agent | Role | Capabilities |
|-------|------|--------------|
| **Planner** | Project planning | Requirements analysis, task decomposition, milestone creation |
| **Product Manager** | Requirements | User stories, acceptance criteria, prioritization |
| **Architect** | System design | Architecture, API design, data modeling, ADRs |
| **Backend** | API implementation | REST/gRPC, business logic, database, auth |
| **Frontend** | UI implementation | React/Next.js, state management, UX |
| **Database** | Data layer | Schema design, migrations, optimization |
| **QA** | Testing | Test planning, automation, quality gates |
| **Security** | Security | Threat modeling, reviews, compliance |
| **DevOps** | Infrastructure | CI/CD, Kubernetes, monitoring |
| **Reviewer** | Quality gates | Code review, architecture review |

## Configuration

Key environment variables (see `.env.example`):

```bash
# Database
DATABASE_URL=postgresql+asyncpg://user:pass@host:5432/db
REDIS_URL=redis://host:6379/0
QDRANT_URL=http://host:6333
NEO4J_URI=bolt://host:7687

# LLM Providers
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-...

# Security
SECRET_KEY=your-secret-key
JWT_EXPIRATION_HOURS=24

# Integrations
GITHUB_TOKEN=ghp_...
KUBECONFIG=/path/to/kubeconfig
```

## API Documentation

API docs available at `/docs` (Swagger UI) and `/redoc` (ReDoc).

Key endpoints:
- `POST /api/v1/projects` - Create project
- `POST /api/v1/workflows` - Create workflow
- `POST /api/v1/workflows/{id}/execute` - Execute workflow
- `GET /api/v1/workflows/{id}/status` - Get workflow status
- `POST /api/v1/rag/query` - Query RAG pipeline
- `WS /api/v1/ws/workflow/{id}` - Real-time workflow updates

## Monitoring

### Metrics (Prometheus/Grafana)
- Workflow execution duration, success rate
- Agent performance (tokens, cost, latency)
- RAG retrieval quality
- System resources (CPU, memory, disk)

### Logs (Loki)
- Structured JSON logs
- Query by service, level, trace ID

### Traces (Tempo)
- Distributed tracing via OpenTelemetry
- Workflow and agent execution traces

## Testing

```bash
# Backend tests
cd apps/backend
pytest --cov=src --cov-report=html

# Frontend tests
cd apps/frontend
npm run test:coverage

# Integration tests
pytest tests/integration/

# E2E tests
pytest tests/e2e/
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make changes with tests
4. Run linting: `ruff check . && mypy apps/backend/src`
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

- Documentation: `/docs`
- Issues: GitHub Issues
- Discussions: GitHub Discussions