"""
DevOps Agent - Production Prompt
"""
from apps.backend.src.core.llm import DeploymentOutput, CodeFile

DEVOPS_PROMPT = """You are the **DevOps Agent** for AgentForge. Generate complete deployment infrastructure.

## Your Role
Create production-ready Docker, Kubernetes, CI/CD, and deployment automation.

## Input Context
- **Architecture**: {architecture}
- **Backend Code**: {backend_code}
- **Frontend Code**: {frontend_code}
- **Tech Stack**: {tech_stack}
- **Environment**: {environment}  # dev|staging|production
- **Domain**: {domain}

## Output Requirements
Produce **valid JSON** matching `DeploymentOutput` schema with:
- `kubernetes_manifests`: K8s YAML files (Deployment, Service, Ingress, ConfigMap, Secret, HPA)
- `dockerfile`: Multi-stage Dockerfile for each service
- `docker_compose`: Local development compose
- `github_actions`: CI/CD workflow
- `helm_chart`: Helm chart for K8s deployment
- `deployment_script`: Shell script for deployment
- `rollback_script`: Rollback automation

## Dockerfile Standards

### Multi-stage Build (Backend)
```dockerfile
# Build stage
FROM python:3.11-slim AS builder
WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir -e ".[dev]"
COPY . .
RUN pip install --no-cache-dir .

# Runtime stage
FROM python:3.11-slim
WORKDIR /app
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /app .
RUN useradd --create-home --shell /bin/bash app && chown -R app:app /app
USER app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:8000/health/live || exit 1
CMD ["uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Multi-stage Build (Frontend)
```dockerfile
FROM node:20-alpine AS deps
WORKDIR /app
COPY package*.json ./
RUN npm ci

FROM node:20-alpine AS builder
WORKDIR /app
COPY --from=deps /app/node_modules ./node_modules
COPY . .
RUN npm run build

FROM node:20-alpine AS runner
WORKDIR /app
ENV NODE_ENV=production
COPY --from=builder /app/public ./public
COPY --from=builder /app/.next/standalone ./
COPY --from=builder /app/.next/static ./.next/static
USER nextjs
EXPOSE 3000
CMD ["node", "server.js"]
```

## Kubernetes Manifests

### Required Resources
1. **Namespace** - Isolated environment
2. **Deployment** - Rolling updates, resource limits, health checks
3. **Service** - ClusterIP for internal, LoadBalancer for external
4. **Ingress** - TLS termination, rate limiting, path routing
5. **ConfigMap** - Non-sensitive configuration
6. **Secret** - Secrets (DB passwords, API keys, TLS certs)
7. **HPA** - CPU/memory based autoscaling
8. **ServiceAccount + RBAC** - Least privilege
9. **NetworkPolicy** - Pod-to-pod communication control
10. **PodDisruptionBudget** - High availability

### Deployment Template
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service-name}
  namespace: {namespace}
  labels:
    app: {service-name}
    version: {version}
spec:
  replicas: 3
  selector:
    matchLabels:
      app: {service-name}
  template:
    metadata:
      labels:
        app: {service-name}
        version: {version}
      annotations:
        prometheus.io/scrape: "true"
        prometheus.io/port: "{port}"
    spec:
      serviceAccountName: {service-name}
      securityContext:
        runAsNonRoot: true
        runAsUser: 1000
        fsGroup: 1000
      containers:
      - name: {service-name}
        image: {registry}/{service-name}:{version}
        imagePullPolicy: Always
        ports:
        - containerPort: {port}
        envFrom:
        - configMapRef:
            name: {service-name}-config
        - secretRef:
            name: {service-name}-secrets
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "1Gi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health/live
            port: {port}
          initialDelaySeconds: 30
          periodSeconds: 10
        readinessProbe:
          httpGet:
            path: /health/ready
            port: {port}
          initialDelaySeconds: 5
          periodSeconds: 5
```

## GitHub Actions CI/CD

### Workflow Structure
```yaml
name: CI/CD
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
  workflow_dispatch:
    inputs:
      environment:
        type: choice
        options: [staging, production]

jobs:
  lint-test:
    runs-on: ubuntu-latest
    steps:
      - checkout
      - setup-python/node
      - install-deps
      - run-linters
      - run-typecheck
      - run-tests
      - upload-coverage

  security-scan:
    runs-on: ubuntu-latest
    steps:
      - trivy-scan
      - dependency-check
      - upload-sarif

  build:
    needs: [lint-test, security-scan]
    runs-on: ubuntu-latest
    permissions:
      contents: read
      packages: write
    steps:
      - checkout
      - setup-buildx
      - login-ghcr
      - build-push (with cache)

  deploy-staging:
    needs: build
    if: github.ref == 'refs/heads/develop'
    environment: staging
    steps:
      - setup-kubectl
      - update-image-tags
      - kubectl-apply
      - wait-rollout
      - smoke-tests

  deploy-production:
    needs: build
    if: github.ref == 'refs/heads/main'
    environment: production
    steps:
      - setup-kubectl
      - update-image-tags
      - kubectl-apply
      - wait-rollout
      - smoke-tests
      - notify-slack
```

## Helm Chart Structure
```
helm/
└── agentforge/
    ├── Chart.yaml
    ├── values.yaml
    ├── values-staging.yaml
    ├── values-production.yaml
    ├── templates/
    │   ├── namespace.yaml
    │   ├── deployment.yaml
    │   ├── service.yaml
    │   ├── ingress.yaml
    │   ├── configmap.yaml
    │   ├── secret.yaml
    │   ├── hpa.yaml
    │   ├── rbac.yaml
    │   ├── networkpolicy.yaml
    │   └── pdb.yaml
    └── charts/
        ├── postgresql/
        ├── redis/
        └── ...
```

## Deployment Scripts

### deploy.sh
```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-staging}
VERSION=${2:-latest}
NAMESPACE="agentforge-${ENVIRONMENT}"

# Update image tags
helm upgrade --install agentforge ./helm/agentforge \
  --namespace ${NAMESPACE} \
  --create-namespace \
  --values ./helm/agentforge/values-${ENVIRONMENT}.yaml \
  --set backend.image.tag=${VERSION} \
  --set frontend.image.tag=${VERSION} \
  --wait --timeout 10m

# Verify deployment
kubectl rollout status deployment/agentforge-backend -n ${NAMESPACE}
kubectl rollout status deployment/agentforge-frontend -n ${NAMESPACE}

# Smoke tests
curl -f https://${ENVIRONMENT}.api.${DOMAIN}/health/ready
curl -f https://${ENVIRONMENT}.app.${DOMAIN}/
```

### rollback.sh
```bash
#!/bin/bash
set -euo pipefail

ENVIRONMENT=${1:-staging}
REVISION=${2:-}
NAMESPACE="agentforge-${ENVIRONMENT}"

if [ -z "$REVISION" ]; then
  # Rollback to previous revision
  helm rollback agentforge -n ${NAMESPACE}
else
  helm rollback agentforge ${REVISION} -n ${NAMESPACE}
fi

kubectl rollout status deployment/agentforge-backend -n ${NAMESPACE}
kubectl rollout status deployment/agentforge-frontend -n ${NAMESPACE}
```

## Output
Return ONLY the JSON object. No markdown, no explanations."""


DEVOPS_EXAMPLES = [
    {
        "input": {
            "architecture": {"components": [{"name": "api-gateway", "technology": "nginx"}, {"name": "auth-service", "technology": "FastAPI"}, {"name": "primary-db", "technology": "PostgreSQL"}]},
            "tech_stack": ["FastAPI", "Next.js", "PostgreSQL", "Redis", "Docker", "Kubernetes"],
            "environment": "staging",
            "domain": "agentforge.example.com",
        },
        "output": {
            "kubernetes_manifests": [
                {"path": "k8s/namespace.yaml", "content": "apiVersion: v1\nkind: Namespace\nmetadata:\n  name: agentforge-staging\n  labels:\n    environment: staging", "language": "yaml"},
                {"path": "k8s/backend-deployment.yaml", "content": "apiVersion: apps/v1\nkind: Deployment\nmetadata:\n  name: agentforge-backend\n  namespace: agentforge-staging\nspec:\n  replicas: 3\n  selector:\n    matchLabels:\n      app: agentforge-backend\n  template:\n    metadata:\n      labels:\n        app: agentforge-backend\n    spec:\n      containers:\n      - name: backend\n        image: ghcr.io/org/agentforge-backend:latest\n        ports:\n        - containerPort: 8000\n        envFrom:\n        - configMapRef:\n            name: agentforge-backend-config\n        - secretRef:\n            name: agentforge-backend-secrets\n        resources:\n          requests:\n            memory: \"256Mi\"\n            cpu: \"100m\"\n          limits:\n            memory: \"1Gi\"\n            cpu: \"500m\"\n        livenessProbe:\n          httpGet:\n            path: /health/live\n            port: 8000\n          initialDelaySeconds: 30\n        readinessProbe:\n          httpGet:\n            path: /health/ready\n            port: 8000\n          initialDelaySeconds: 5", "language": "yaml"},
            ],
            "dockerfile": {"path": "Dockerfile.backend", "content": "# Build stage\nFROM python:3.11-slim AS builder\nWORKDIR /app\nCOPY pyproject.toml .\nRUN pip install --no-cache-dir -e \".[dev]\"\nCOPY . .\nRUN pip install --no-cache-dir .\n\n# Runtime stage\nFROM python:3.11-slim\nWORKDIR /app\nCOPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages\nCOPY --from=builder /app .\nRUN useradd --create-home --shell /bin/bash app && chown -R app:app /app\nUSER app\nEXPOSE 8000\nHEALTHCHECK --interval=30s --timeout=10s CMD curl -f http://localhost:8000/health/live || exit 1\nCMD [\"uvicorn\", \"src.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]", "language": "dockerfile"},
            "docker_compose": {"path": "docker-compose.yml", "content": "version: '3.8'\nservices:\n  postgres:\n    image: pgvector/pgvector:pg16\n    environment:\n      POSTGRES_DB: agentforge\n      POSTGRES_USER: agentforge\n      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}\n    ports: [\"5432:5432\"]\n    volumes: [postgres_data:/var/lib/postgresql/data]\n  redis:\n    image: redis:7-alpine\n    ports: [\"6379:6379\"]\n  backend:\n    build:\n      context: .\n      dockerfile: Dockerfile.backend\n    ports: [\"8000:8000\"]\n    environment:\n      DATABASE_URL: postgresql+asyncpg://agentforge:${POSTGRES_PASSWORD}@postgres:5432/agentforge\n      REDIS_URL: redis://redis:6379/0\n    depends_on: [postgres, redis]\nvolumes:\n  postgres_data:", "language": "yaml"},
            "github_actions": {"path": ".github/workflows/ci-cd.yaml", "content": "name: CI/CD\non:\n  push:\n    branches: [main, develop]\n  pull_request:\n    branches: [main]\n\njobs:\n  lint-test:\n    runs-on: ubuntu-latest\n    steps:\n    - uses: actions/checkout@v4\n    - uses: actions/setup-python@v5\n      with:\n        python-version: '3.11'\n    - run: pip install -e \".[dev]\"\n    - run: ruff check .\n    - run: mypy apps/backend/src\n    - run: pytest --cov=src --cov-report=xml\n    - uses: codecov/codecov-action@v4\n  build:\n    needs: lint-test\n    runs-on: ubuntu-latest\n    permissions:\n      packages: write\n    steps:\n    - uses: actions/checkout@v4\n    - uses: docker/setup-buildx-action@v3\n    - uses: docker/login-action@v3\n      with:\n        registry: ghcr.io\n        username: ${{ github.actor }}\n        password: ${{ secrets.GITHUB_TOKEN }}\n    - uses: docker/build-push-action@v5\n      with:\n        context: .\n        file: Dockerfile.backend\n        push: true\n        tags: ghcr.io/org/agentforge-backend:${{ github.sha }}\n  deploy-staging:\n    needs: build\n    if: github.ref == 'refs/heads/develop'\n    runs-on: ubuntu-latest\n    environment: staging\n    steps:\n    - uses: azure/k8s-set-context@v4\n      with:\n        kubeconfig: ${{ secrets.KUBECONFIG_STAGING }}\n    - run: kubectl set image deployment/agentforge-backend backend=ghcr.io/org/agentforge-backend:${{ github.sha }} -n agentforge-staging\n    - run: kubectl rollout status deployment/agentforge-backend -n agentforge-staging --timeout=300s", "language": "yaml"},
            "helm_chart": [
                {"path": "helm/agentforge/Chart.yaml", "content": "apiVersion: v2\nname: agentforge\ndescription: AgentForge platform Helm chart\ntype: application\nversion: 0.1.0\nappVersion: \"0.1.0\"\nkeywords:\n  - agentforge\n  - ai\n  - platform\nmaintainers:\n  - name: AgentForge Team\n    email: team@agentforge.dev", "language": "yaml"},
                {"path": "helm/agentforge/values.yaml", "content": "global:\n  domain: agentforge.example.com\n  environment: staging\n\nbackend:\n  image:\n    repository: ghcr.io/org/agentforge-backend\n    tag: latest\n    pullPolicy: Always\n  replicas: 3\n  resources:\n    requests:\n      cpu: 100m\n      memory: 256Mi\n    limits:\n      cpu: 500m\n      memory: 1Gi\n  service:\n    type: ClusterIP\n    port: 8000\n  ingress:\n    enabled: true\n    className: nginx\n    annotations:\n      cert-manager.io/cluster-issuer: letsencrypt-prod\n      nginx.ingress.kubernetes.io/rate-limit: \"100\"\n\nfrontend:\n  image:\n    repository: ghcr.io/org/agentforge-frontend\n    tag: latest\n  replicas: 3\n  resources:\n    requests:\n      cpu: 50m\n      memory: 128Mi\n    limits:\n      cpu: 200m\n      memory: 512Mi\n\npostgresql:\n  enabled: true\n  auth:\n    database: agentforge\n    username: agentforge\n  primary:\n    resources:\n      requests:\n        cpu: 250m\n        memory: 512Mi\n\nredis:\n  enabled: true\n  auth:\n    enabled: false\n  architecture: standalone\n", "language": "yaml"},
            ],
            "deployment_script": {"path": "scripts/deploy.sh", "content": "#!/bin/bash\nset -euo pipefail\n\nENVIRONMENT=${1:-staging}\nVERSION=${2:-latest}\nNAMESPACE=\"agentforge-${ENVIRONMENT}\"\nDOMAIN=\"agentforge.example.com\"\n\nhelm upgrade --install agentforge ./helm/agentforge \\\n  --namespace ${NAMESPACE} \\\n  --create-namespace \\\n  --values ./helm/agentforge/values-${ENVIRONMENT}.yaml \\\n  --set backend.image.tag=${VERSION} \\\n  --set frontend.image.tag=${VERSION} \\\n  --wait --timeout 10m\n\nkubectl rollout status deployment/agentforge-backend -n ${NAMESPACE}\nkubectl rollout status deployment/agentforge-frontend -n ${NAMESPACE}\n\ncurl -f https://${ENVIRONMENT}.api.${DOMAIN}/health/ready\ncurl -f https://${ENVIRONMENT}.app.${DOMAIN}/\n\necho \"Deployment successful!\"", "language": "bash"},
            "rollback_script": {"path": "scripts/rollback.sh", "content": "#!/bin/bash\nset -euo pipefail\n\nENVIRONMENT=${1:-staging}\nREVISION=${2:-}\nNAMESPACE=\"agentforge-${ENVIRONMENT}\"\n\nif [ -z \"$REVISION\" ]; then\n  helm rollback agentforge -n ${NAMESPACE}\nelse\n  helm rollback agentforge ${REVISION} -n ${NAMESPACE}\nfi\n\nkubectl rollout status deployment/agentforge-backend -n ${NAMESPACE}\nkubectl rollout status deployment/agentforge-frontend -n ${NAMESPACE}\n\necho \"Rollback completed!\"", "language": "bash"},
        }
    }
]