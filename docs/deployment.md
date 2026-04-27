# Deployment

## Environments

### Staging

Deployed automatically on every push to the `staging` branch.

```text
git push origin staging  →  CI passes  →  Deploy to staging
```

### Production

Deployed automatically on every push to the `main` branch.

```text
git push origin main  →  CI passes  →  Deploy to production
```

## Workflow

The recommended flow for shipping a feature:

1. Create a `feature/*` branch from `staging`
2. Develop and push — CI runs automatically
3. Open a PR to `staging` — reviewers check code + CI status
4. Merge to `staging` — auto-deploy to staging environment
5. Test on staging
6. Merge `staging` into `main` — auto-deploy to production

## Docker

Build and run locally:

```bash
docker build -t flask-cicd-demo .
docker run -p 5000:5000 flask-cicd-demo
```

## Health Check

Both environments expose a health endpoint:

```bash
curl https://your-server/health
# {"status": "healthy"}
```
