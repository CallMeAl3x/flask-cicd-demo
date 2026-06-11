# Flask CI/CD Demo

A simple Flask REST API with a complete CI/CD pipeline using GitHub Actions.

## Architecture

```
main (production) ← staging ← feature branches
```

### Branching Strategy

| Branch | Purpose | Deployment |
|--------|---------|------------|
| `main` | Production-ready code | Auto-deploy to production |
| `staging` | Pre-production testing | Auto-deploy to staging |
| `feature/*` | Development | CI only (lint + test + security) |

### CI/CD Pipeline

Every push and PR triggers:
- **Lint**: Black, isort, Flake8, Mypy
- **Test**: pytest with coverage (Python 3.11 & 3.12)
- **Security**: Bandit static analysis

Deployment flows:
- Push to `staging` → CI + deploy to staging
- Push to `main` → CI + deploy to production + **deploy to Kubernetes (DigitalOcean)**

### Kubernetes Deployment

On every push to `main`, the image is built and pushed to **GHCR**
(`ghcr.io/callmeal3x/flask-cicd-demo`), then deployed to a managed **DigitalOcean Kubernetes** cluster
(2 replicas, `LoadBalancer` service, liveness/readiness probes on `/health`). The `deploy-k8s` job waits
for `kubectl rollout status` to confirm success.

```bash
# Manifests live in k8s/ — test them on a local cluster (minikube/kind):
kubectl apply -k k8s/
kubectl get pods
kubectl port-forward svc/flask-app 5000:80
curl localhost:5000/health   # {"status":"healthy"}
```

Cluster setup is documented in [`k8s/SETUP-DIGITALOCEAN.md`](k8s/SETUP-DIGITALOCEAN.md).

## Local Development

```bash
# Install dependencies
pip install -r requirements-dev.txt

# Run the app
python run.py

# Run tests
pytest

# Code quality
black .
isort .
flake8 app/ tests/
mypy app/
bandit -r app/
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | API info |
| GET | `/health` | Health check |
| GET | `/tasks` | List all tasks |
| POST | `/tasks` | Create a task |
| PUT | `/tasks/<id>` | Update a task |
| DELETE | `/tasks/<id>` | Delete a task |


