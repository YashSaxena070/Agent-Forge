# AgentForge ⚡

> **Autonomous AI Software Development & Engineering Platform**  
> An enterprise-grade, multi-agent platform designed to automate the end-to-end software development lifecycle—from requirements analysis, system architecture, and fullstack coding to quality assurance, security reviews, and production deployment.

---

## 📑 Table of Contents

- [Overview](#-overview)
- [System Architecture](#-system-architecture)
- [Subsystems & Capabilities](#-subsystems--capabilities)
  - [1. Enterprise Core Backend (Spring Boot 3.4)](#1-enterprise-core-backend-spring-boot-34)
  - [2. Multi-Agent Orchestration & AI Services (FastAPI + LangGraph)](#2-multi-agent-orchestration--ai-services-fastapi--langgraph)
  - [3. Frontend Dashboard (Next.js 14)](#3-frontend-dashboard-nextjs-14)
  - [4. Hybrid RAG & 4-Tier Memory](#4-hybrid-rag--4-tier-memory)
  - [5. Infrastructure & Full Observability Stack](#5-infrastructure--full-observability-stack)
- [Project Directory Structure](#-project-directory-structure)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Quick Start with Docker Compose](#quick-start-with-docker-compose)
  - [Running Individual Services Locally](#running-individual-services-locally)
- [Environment Configuration](#-environment-configuration)
- [API Documentation](#-api-documentation)
- [Testing](#-testing)
- [Production Deployment](#-production-deployment)
- [License](#-license)

---

## 🔭 Overview

AgentForge bridges enterprise software engineering governance with cutting-edge autonomous AI agents:

1. **Enterprise Control Plane**: Written in **Java 21 / Spring Boot 3.4**, providing multi-tenant workspace isolation, role-based access control (RBAC), multi-factor authentication (TOTP & WebAuthn / Passkeys), Open Policy Agent (OPA) fine-grained authorization, HashiCorp Vault secrets management, tamper-evident cryptographic audit logs, and automated disaster recovery.
2. **Autonomous Agent Plane**: Powered by **Python, FastAPI, and LangGraph**, running a coordinated team of 10 specialized agents that brainstorm, design, build, test, and package applications with human-in-the-loop review gates.
3. **Hybrid RAG & Memory**: Blending dense vector retrieval (Qdrant) and knowledge graphs (Neo4j) with tiered caching (Redis) and relational persistence (PostgreSQL) for deep contextual awareness.
4. **Developer UI**: A modern **Next.js 14** web console featuring real-time WebSocket state streaming, interactive workflow graph visualization, and agent approval dashboards.

---

## 🏛 System Architecture

```
                                  ┌────────────────────────────────────────┐
                                  │       Client / Developer Browser       │
                                  └───────────────────┬────────────────────┘
                                                      │ HTTPS / WSS
                                                      ▼
                       ┌──────────────────────────────────────────────────────────────┐
                       │                   API Gateway & Ingress                      │
                       └──────────────┬───────────────────────────────┬───────────────┘
                                      │                               │
            ┌─────────────────────────┴─────────┐   ┌─────────────────┴────────────────────────┐
            │   Enterprise Core Backend         │   │   AI & Multi-Agent Orchestration         │
            │   (Spring Boot 3.4 / Java 21)     │   │   (FastAPI / LangGraph / Python)         │
            ├───────────────────────────────────┤   ├──────────────────────────────────────────┤
            │ • Multi-tenant Workspaces         │   │ • 10 Specialized Software Agents         │
            │ • RBAC & OPA Fine-grained Auth    │   │ • LangGraph StateMachine Workflows       │
            │ • MFA: TOTP & WebAuthn Passkeys   │   │ • Model Context Protocol (MCP) Tools     │
            │ • HashiCorp Vault Envelope Encrypt│   │ • Human-in-the-loop Approval Nodes       │
            │ • SHA-256 Audit Hash Chain        │   │ • Hybrid RAG (Qdrant Vector + Neo4j)     │
            │ • Disaster Recovery & Backups     │   │ • Temporal Durable Workflow Engine       │
            └─────────────────┬─────────────────┘   └─────────────────┬────────────────────────┘
                              │                                       │
                              └───────────────────┬───────────────────┘
                                                  ▼
                       ┌──────────────────────────────────────────────────────────────┐
                       │                     Data & Memory Layer                      │
                       ├──────────────────────┬───────────────────────┬───────────────┤
                       │  PostgreSQL (Data)   │  Redis (Sessions)     │  Qdrant (RAG) │
                       │  pgvector (Vectors)  │  Neo4j (Knowledge)    │  MinIO (S3)   │
                       └──────────────────────┴───────────────────────┴───────────────┘
                                                  ▲
                                                  │ Telemetry
                       ┌──────────────────────────┴───────────────────────────────────┐
                       │               Observability & Monitoring Stack               │
                       ├──────────────────────┬───────────────────────┬───────────────┤
                       │  Prometheus (Metrics)│  Grafana (Dashboards) │  Loki (Logs)  │
                       │  OpenTelemetry (OTel)│  Tempo (APM Tracing)  │  Micrometer   │
                       └──────────────────────┴───────────────────────┴───────────────┘
```

---

## 🧩 Subsystems & Capabilities

### 1. Enterprise Core Backend (Spring Boot 3.4)
- **Multi-Tenant Hierarchy**: Strict isolation between Organizations, Workspaces, and Projects with tenant context propagators (`WorkspaceContextFilter`, `WorkspaceContextHolder`).
- **Identity & Access Management (IAM)**: OAuth2 Resource Server, OIDC / SAML SSO integration, JWT access & refresh tokens with rotation and revocation blacklist.
- **Enterprise MFA / Passkeys**:
  - RFC 6238 TOTP (Google Authenticator) with QR generation and encrypted secret storage.
  - FIDO2 / WebAuthn passkey registration and attestation via Yubico WebAuthn Server.
  - Cryptographically secure emergency backup recovery codes.
- **Fine-Grained Authorization (OPA)**: Open Policy Agent client evaluating dynamic declarative policies for critical project operations.
- **Secrets & Data Protection**: HashiCorp Vault transit engine integration, AES-256-GCM envelope encryption for sensitive credentials (`CryptoUtil`).
- **Cryptographic Audit Logs**: Tamper-evident ledger linking log events via SHA-256 hash chains (`AuditService`).
- **Disaster Recovery**: Automated scheduled database dumps (`pg_dump`), GZIP compression, SHA-256 integrity verification, and instant restore pipelines (`BackupService`).

### 2. Multi-Agent Orchestration & AI Services (FastAPI + LangGraph)
- **10 Specialized Engineering Agents**:
  | Agent | Primary Responsibilities |
  |---|---|
  | **Planner** | Requirements parsing, epic decomposition, milestone scheduling |
  | **Product Manager** | User stories, acceptance criteria, priority matrix |
  | **Architect** | Architecture decisions (ADRs), API contract definitions, data models |
  | **Backend** | Endpoint generation, business logic, persistence layers, auth integration |
  | **Frontend** | React/Next.js component implementation, state management, styling |
  | **Database** | Migration generation (Flyway/Alembic), query optimization, indexing |
  | **QA** | Unit, integration, and E2E test plan generation and execution |
  | **Security** | OWASP Top 10 threat modeling, static code analysis, dependency audits |
  | **DevOps** | Dockerfile creation, Helm / K8s manifests, CI/CD pipeline automation |
  | **Reviewer** | Cross-cutting code reviews, architectural quality gates, lint enforcement |
- **Durable Execution & Checkpoints**: Temporal and LangGraph `MemorySaver` checkpointers enable resumable workflows, safe rollbacks, and interactive human-in-the-loop approval.
- **Model Context Protocol (MCP)**: Tool integration for GitHub, Docker daemon, Kubernetes clusters, local filesystem, and web research.

### 3. Frontend Dashboard (Next.js 14)
- Built on the Next.js App Router with TypeScript, Tailwind CSS, and Radix UI components.
- Interactive workflow graphs visualizing agent node states, token consumption, and intermediate code diffs.
- Live streaming execution updates over WebSockets.
- Human review gates allowing engineers to approve, revise, or reject agent decisions.

### 4. Hybrid RAG & 4-Tier Memory
- **Short-Term Memory**: Redis-backed conversation cache for fast agent reasoning context.
- **Long-Term Memory**: PostgreSQL entity storage tracking historical projects, builds, and audit events.
- **Semantic Vector Memory**: Qdrant vector database indexing codebase symbols, documentation, and pull request history.
- **Relationship Knowledge Graph**: Neo4j graph database storing dependencies, microservice call graphs, and architectural topologies.

### 5. Infrastructure & Full Observability Stack
- **Prometheus & Micrometer**: SLI/SLO latency timers, error counters, and agent token usage metrics.
- **Grafana**: Pre-configured dashboards for system health, agent KPIs, and cluster metrics.
- **Loki & Promtail**: Centralized structured JSON logging across all backend and agent microservices.
- **Tempo & OpenTelemetry**: Distributed tracing linking HTTP requests to downstream LLM agent tool calls.

---

## 📁 Project Directory Structure

```
AgentForge/
├── backend/                      # Enterprise Java Core Backend
│   ├── src/main/java/com/agentforge/backend/
│   │   ├── audit/                # Cryptographic audit logging & hash chaining
│   │   ├── auth/                 # Authentication, JWT, and session management
│   │   ├── common/               # ApiResponse, exceptions, crypto utilities
│   │   ├── config/               # Enterprise RSA keys & OAuth2 security configs
│   │   ├── disaster/             # Automated backup & restore engine
│   │   ├── domain/               # JPA entities (User, Org, Project, MFA)
│   │   ├── mfa/                  # TOTP & WebAuthn / Passkeys controller & services
│   │   ├── monitoring/           # Micrometer SLI metrics & Prometheus hooks
│   │   ├── organization/         # Organization & membership management
│   │   ├── project/              # Project and project-member services
│   │   ├── security/             # Spring Security, OPA client, Vault client
│   │   └── tenant/               # Workspace multi-tenancy & context filtering
│   ├── src/main/resources/       # application.yml, DB migrations (Flyway V1..V10)
│   ├── pom.xml                   # Maven dependencies (Spring Boot 3.4.2, Java 21)
│   └── mvnw.cmd / mvnw           # Maven wrapper scripts
│
├── ai-services/                  # Agentic Microservice Suite
│   ├── agent-service/            # Core FastAPI agent runtime & state graphs
│   ├── planner-service/          # Planning & task decomposition service
│   ├── workflow-service/         # Workflow graph dispatcher
│   ├── rag-service/              # Vector & graph search engine
│   ├── mcp-service/              # Model Context Protocol tools
│   └── shared-ai/                # Shared LLM abstractions and prompts
│
├── apps/                         # Fullstack Application Modules
│   ├── backend/                  # Python FastAPI service for multi-agent execution
│   │   ├── src/                  # Agents, orchestration nodes, API v1, RAG
│   │   ├── alembic/              # Database schema migrations
│   │   └── requirements.txt      # Python dependencies
│   └── frontend/                 # Next.js 14 Dashboard
│       ├── src/                  # App router pages, components, lib
│       ├── tailwind.config.ts    # Tailwind styling config
│       └── package.json          # Node dependencies
│
├── services/
│   └── shared/                   # Shared Python schemas, config, telemetry, & utils
│
├── infra/                        # Infrastructure Configurations
│   ├── docker/                   # Dockerfiles for backend, frontend, and workers
│   └── kubernetes/               # K8s base manifests, RBAC, deployments, ingress
│
├── monitoring/                   # Observability Stack
│   ├── prometheus/               # Prometheus scrape configs & alert rules
│   ├── grafana/                  # Dashboards (AgentForge Overview) & datasources
│   ├── loki/                     # Loki log aggregation configs
│   └── tempo/                    # Tempo tracing configs
│
├── docker-compose.yml            # Full production stack (apps + databases + monitoring)
├── docker-compose.dev.yml        # Development environment stack
├── Makefile                      # Quick developer CLI shortcuts
├── pyproject.toml                # Python workspace metadata
└── README.md                     # Project documentation
```

---

## 🚀 Getting Started

### Prerequisites

Ensure the following tools are installed on your machine:
- **Java Development Kit (JDK) 21+** (`java -version`)
- **Python 3.11+** (`python --version`)
- **Node.js 20+** & **npm** / **pnpm** (`node -v`)
- **Docker** & **Docker Compose** (`docker compose version`)

---

### Quick Start with Docker Compose

To spin up all databases, message brokers, and observability infrastructure:

```bash
# 1. Clone the repository
git clone https://github.com/your-org/AgentForge.git
cd AgentForge

# 2. Copy the sample environment file
cp .env.example .env

# 3. Start the infrastructure containers
docker compose up -d postgres redis qdrant neo4j minio
```

---

### Running Individual Services Locally

#### 1. Java Enterprise Backend (`backend/`)
```bash
cd backend

# Compile and verify tests
./mvnw clean compile -DskipTests   # Windows: .\mvnw.cmd clean compile -DskipTests

# Run the Spring Boot application
./mvnw spring-boot:run              # Windows: .\mvnw.cmd spring-boot:run
```
*The Spring Boot API runs at `http://localhost:8080/api`.*

#### 2. AI Agent Service (`ai-services/agent-service/`)
```bash
cd ai-services/agent-service

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate          # Windows: .\.venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Start the FastAPI service
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```
*Health check is available at `http://localhost:8000/health`.*

#### 3. Frontend Dashboard (`apps/frontend/`)
```bash
cd apps/frontend

# Install dependencies
npm install

# Start development server
npm run dev
```
*The dashboard opens at `http://localhost:3000`.*

---

## ⚙️ Environment Configuration

Copy `.env.example` to `.env` in the root and configure required credentials:

```ini
# Database & Cache
DATABASE_URL=jdbc:postgresql://localhost:5432/agentforge
DATABASE_USERNAME=agentforge
DATABASE_PASSWORD=agentforge_dev
REDIS_HOST=localhost
REDIS_PORT=6379

# Vector & Graph Databases
QDRANT_URL=http://localhost:6333
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=agentforge_dev

# JWT Security
JWT_SECRET=your-256-bit-secret-key-base64-encoded==
JWT_ACCESS_TOKEN_EXPIRATION=900000        # 15 minutes
JWT_REFRESH_TOKEN_EXPIRATION=2592000000    # 30 days

# LLM Providers
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...

# OPA & Vault Integration
OPA_URL=http://localhost:8181
VAULT_URL=http://localhost:8200
VAULT_TOKEN=your-vault-token
```

---

## 📖 API Documentation

Once services are running, interactive API documentation is available at:

| Service | Swagger UI / OpenAPI | Endpoint |
|---|---|---|
| **Enterprise Backend** | `http://localhost:8080/api/swagger-ui.html` | `/api/v1/**` |
| **AI Agent Service** | `http://localhost:8000/docs` | `/agent/**`, `/health` |
| **FastAPI Orchestrator** | `http://localhost:8001/docs` | `/api/v1/**` |

---

## 🧪 Testing

```bash
# Run Java Spring Boot unit & integration tests
cd backend
./mvnw test                         # Windows: .\mvnw.cmd test

# Run Python AI service tests
cd apps/backend
pytest tests/ -v

# Run Frontend linting & tests
cd apps/frontend
npm run lint
npm run test
```

---

## 🚢 Production Deployment

### Docker Container Builds

```bash
# Build backend container
docker build -t agentforge/backend:latest -f infra/docker/Dockerfile.backend .

# Build frontend container
docker build -t agentforge/frontend:latest -f infra/docker/Dockerfile.frontend .

# Build agent worker container
docker build -t agentforge/worker:latest -f infra/docker/Dockerfile.worker .
```

### Kubernetes Manifest Deployment

```bash
# Apply namespace, RBAC, and base manifests
kubectl apply -f infra/kubernetes/base/namespace.yaml
kubectl apply -f infra/kubernetes/base/rbac.yaml
kubectl apply -f infra/kubernetes/base/secrets.yaml
kubectl apply -f infra/kubernetes/base/backend-deployment.yaml
kubectl apply -f infra/kubernetes/base/frontend-deployment.yaml
kubectl apply -f infra/kubernetes/base/ingress.yaml
```

---

## 📄 License

This project is licensed under the [MIT License](LICENSE).
