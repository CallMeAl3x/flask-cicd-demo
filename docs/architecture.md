# Architecture

## Branching Strategy

```text
feature/* ──► staging ──► main
              (pre-prod)    (production)
```

| Branch | Purpose | Triggers |
|--------|---------|----------|
| `main` | Production-ready code | CI + Deploy prod |
| `staging` | Pre-production testing | CI + Deploy staging |
| `feature/*` | Development | CI only |

## CI Pipeline

Every push and pull request runs **3 parallel jobs**:

```text
┌─────────────┐  ┌─────────────┐  ┌─────────────┐
│  Code Lint   │  │    Tests     │  │  Security   │
│              │  │              │  │             │
│ - Black      │  │ - pytest     │  │ - Bandit    │
│ - isort      │  │ - coverage   │  │             │
│ - Flake8     │  │ - Python     │  │             │
│ - Mypy       │  │   3.11/3.12  │  │             │
└─────────────┘  └─────────────┘  └─────────────┘
```

## Project Structure

```text
flask-cicd-demo/
├── app/
│   ├── __init__.py      # Application factory
│   ├── config.py        # Environment configs
│   └── routes.py        # API endpoints
├── tests/
│   ├── conftest.py      # Fixtures
│   ├── test_config.py   # Config tests
│   └── test_routes.py   # API tests
├── docs/                # Sphinx documentation
├── .github/workflows/   # CI/CD pipelines
├── Dockerfile
├── requirements.txt
└── requirements-dev.txt
```
