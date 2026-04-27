# Explication complete du projet CI/CD

## Vue d'ensemble

Ce projet est une **API REST Flask** (gestion de taches) accompagnee d'un pipeline **CI/CD complet** via GitHub Actions. L'objectif est de demontrer un workflow professionnel : du code pousse sur une branche jusqu'au deploiement automatique, en passant par les tests, la qualite de code, la securite et la documentation auto-generee.

**Repo** : https://github.com/CallMeAl3x/flask-cicd-demo
**Documentation** : https://callmeal3x.github.io/flask-cicd-demo/

---

## 1. L'application Flask

### Structure du code

```
app/
├── __init__.py    → Factory pattern (create_app)
├── config.py      → Configurations par environnement
└── routes.py      → Endpoints de l'API
```

### Factory Pattern (`app/__init__.py`)

L'application utilise le **Application Factory pattern** de Flask. Au lieu de creer l'app globalement, on passe par une fonction `create_app(config_name)` qui :

1. Cree l'instance Flask
2. Charge la configuration selon l'environnement (`production`, `staging`, `testing`)
3. Enregistre les blueprints (routes)

```python
def create_app(config_name: str = "production") -> Flask:
    app = Flask(__name__)
    app.config.from_object(configs.get(config_name, configs["production"]))
    app.register_blueprint(api)
    return app
```

**Pourquoi ce pattern ?** Il permet de creer plusieurs instances avec des configs differentes — indispensable pour les tests (on cree une app en mode `testing` sans toucher a la prod).

### Configuration (`app/config.py`)

Trois classes heritent de `BaseConfig` :

| Classe | `DEBUG` | `TESTING` | Utilisation |
|--------|---------|-----------|-------------|
| `ProductionConfig` | `False` | `False` | Deploiement prod |
| `StagingConfig` | `True` | `False` | Pre-production |
| `TestingConfig` | `False` | `True` | Tests pytest |

`SECRET_KEY` est lu depuis une variable d'environnement avec un fallback — en prod, on la definirait via un secret GitHub ou une variable d'environnement serveur.

### Routes API (`app/routes.py`)

L'API expose 6 endpoints CRUD pour gerer des taches :

| Methode | Endpoint | Description | Code retour |
|---------|----------|-------------|-------------|
| `GET` | `/` | Info de l'API | 200 |
| `GET` | `/health` | Health check | 200 |
| `GET` | `/tasks` | Lister les taches | 200 |
| `POST` | `/tasks` | Creer une tache | 201 / 400 |
| `PUT` | `/tasks/<id>` | Modifier une tache | 200 / 404 |
| `DELETE` | `/tasks/<id>` | Supprimer une tache | 200 / 404 |

Les taches sont stockees en memoire (liste Python). C'est volontairement simple — l'objectif est la CI/CD, pas la persistence.

### Point d'entree (`run.py`)

```python
config = os.environ.get("FLASK_ENV", "production")
app = create_app(config)
```

Lit la variable `FLASK_ENV` pour choisir la config. Par defaut : production.

---

## 2. Strategie de branches

```
feature/ma-feature ──► staging ──► main
                       (pre-prod)   (production)
```

### Flux de travail

1. **Creer une branche** `feature/*` depuis `staging`
2. **Developper** et pousser — le CI tourne automatiquement
3. **Ouvrir une PR** vers `staging` — les reviewers verifient le code + le statut CI
4. **Merger dans staging** — deploiement automatique sur l'environnement staging
5. **Tester sur staging** — validation fonctionnelle
6. **Merger staging dans main** — deploiement automatique en production

### Pourquoi deux branches ?

- **staging** : permet de tester les changements dans un environnement similaire a la prod avant de les deployer reellement
- **main** : represente toujours le code en production — chaque commit sur main declenche un deploy prod

---

## 3. Pipeline CI/CD (GitHub Actions)

Le projet contient **4 workflows** dans `.github/workflows/` :

### 3.1 CI Pipeline (`ci.yml`)

**Declencheur** : chaque push ou PR sur `main` et `staging`

Ce workflow execute **3 jobs en parallele** :

#### Job 1 : Code Quality (lint)

Verifie la qualite du code sans l'executer :

| Outil | Role | Ce qu'il verifie |
|-------|------|-----------------|
| **Black** | Formateur | Le code est-il formate selon le standard Black ? (ligne max 88 car.) |
| **isort** | Tri des imports | Les imports sont-ils tries et groupes correctement ? |
| **Flake8** | Linter | Erreurs de style PEP8, variables inutilisees, imports manquants |
| **Mypy** | Type checker | Les annotations de type sont-elles coherentes ? |

```yaml
- name: Black (formatting)
  run: black --check .        # --check = ne modifie pas, echoue si mal formate

- name: isort (import order)
  run: isort --check-only .

- name: Flake8 (linting)
  run: flake8 app/ tests/ --max-line-length=88 --extend-ignore=E203

- name: Mypy (type checking)
  run: mypy app/
```

#### Job 2 : Tests

Execute les tests sur **2 versions de Python** (3.11 et 3.12) grace a une **matrix strategy** :

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
```

Cela cree 2 jobs paralleles, un par version. Si les tests passent sur 3.11 mais echouent sur 3.12 (ou l'inverse), on le voit immediatement.

Les tests sont executes avec **pytest** et generent un **rapport de couverture** (coverage) :

```yaml
- name: Run tests with coverage
  run: pytest   # la config dans pyproject.toml ajoute --cov=app automatiquement
```

Le rapport de couverture est uploade comme **artifact** GitHub Actions (telechargeable depuis l'interface).

#### Job 3 : Security Scan

**Bandit** analyse statiquement le code Python pour detecter des failles de securite courantes :

- Utilisation de `eval()` ou `exec()`
- Requetes HTTP sans verification SSL
- Mots de passe en dur
- Injections SQL
- Utilisation de fonctions dangereuses

```yaml
- name: Bandit (security linter)
  run: bandit -r app/ -f json -o bandit-report.json || true

- name: Bandit report
  run: bandit -r app/
```

Le rapport JSON est aussi uploade comme artifact.

#### Workflow reusable (`workflow_call`)

Le CI est defini comme **reusable workflow** grace a `workflow_call:` dans le trigger. Cela permet aux workflows de deploy de l'appeler directement :

```yaml
# Dans deploy-staging.yml
jobs:
  ci:
    uses: ./.github/workflows/ci.yml   # ← appelle le CI complet
  deploy-staging:
    needs: ci                           # ← attend que le CI passe
```

### 3.2 Deploy Staging (`deploy-staging.yml`)

**Declencheur** : push sur `staging` uniquement

```
Push sur staging → CI complet → Deploy staging
```

Le job de deploy :
1. **Depend du CI** (`needs: ci`) — si le CI echoue, pas de deploy
2. Utilise l'**environment** GitHub `staging` — permet de configurer des secrets/variables specifiques
3. **Build l'app** en mode staging et lance un **smoke test** (health check)
4. **Simule le deploiement** (dans un vrai projet : SSH vers le VPS, docker compose, etc.)

### 3.3 Deploy Production (`deploy-prod.yml`)

**Declencheur** : push sur `main` uniquement

Identique au staging avec une etape supplementaire : **creation d'un backup** avant le deploy. En production, on ajouterait typiquement :
- Sauvegarde de la base de donnees
- Deploiement blue/green ou canary
- Notification Slack/Discord

### 3.4 Documentation (`docs.yml`)

**Declencheur** : push ou PR sur `main` et `staging`

1. **Build** la documentation Sphinx a partir du code source
2. **Upload** comme artifact (telechargeable)
3. **Deploy sur GitHub Pages** (uniquement depuis `main`)

```yaml
- name: Build Sphinx documentation
  run: sphinx-build -b html docs/ docs/_build/html -W   # -W = warnings = erreurs
```

Le flag `-W` fait echouer le build si la doc contient des warnings — ca force a maintenir une doc propre.

---

## 4. Les tests

### Structure

```
tests/
├── conftest.py       → Fixtures partagees
├── test_config.py    → Tests des configurations
└── test_routes.py    → Tests des endpoints API
```

### Fixtures (`conftest.py`)

```python
@pytest.fixture
def app():
    app = create_app("testing")  # ← utilise TestingConfig
    yield app

@pytest.fixture
def client(app):
    return app.test_client()     # ← client HTTP de test Flask
```

Le `test_client()` de Flask permet de faire des requetes HTTP sans lancer de serveur — les tests sont rapides et isoles.

### Ce qui est teste

**12 tests** couvrant **98% du code** :

- **Config** (3 tests) : verifie que chaque environnement a les bons flags (`DEBUG`, `TESTING`)
- **Routes** (9 tests) : teste chaque endpoint avec les cas normaux ET les cas d'erreur (404, 400)

Exemples :
```python
def test_create_task(client):
    response = client.post("/tasks", data=json.dumps({"title": "Test"}), ...)
    assert response.status_code == 201

def test_create_task_missing_title(client):      # ← cas d'erreur
    response = client.post("/tasks", data=json.dumps({}), ...)
    assert response.status_code == 400
```

### Configuration pytest (`pyproject.toml`)

```toml
[tool.pytest.ini_options]
testpaths = ["tests"]
addopts = "--cov=app --cov-report=term-missing --cov-report=xml"
```

- `--cov=app` : mesure la couverture du dossier `app/`
- `--cov-report=term-missing` : affiche les lignes non couvertes dans le terminal
- `--cov-report=xml` : genere un `coverage.xml` pour les outils CI

---

## 5. Mesures de qualite du code

### Outils et leur role

| Outil | Type | Fichier de config | Ce qu'il empeche |
|-------|------|-------------------|-----------------|
| **Black** | Formateur | `pyproject.toml` | Code mal formate, debats de style |
| **isort** | Tri imports | `pyproject.toml` | Imports desorganises |
| **Flake8** | Linter | CLI args | Erreurs PEP8, code mort |
| **Mypy** | Type checker | `pyproject.toml` | Erreurs de types a l'execution |
| **pytest-cov** | Couverture | `pyproject.toml` | Code non teste |
| **Bandit** | Securite | `pyproject.toml` | Failles de securite connues |

### Configuration dans `pyproject.toml`

```toml
[tool.black]
line-length = 88                # Standard Black

[tool.isort]
profile = "black"               # Compatible avec le formatage Black

[tool.mypy]
python_version = "3.12"
warn_return_any = true          # Alerte si une fonction retourne Any
warn_unused_configs = true

[tool.bandit]
exclude_dirs = ["tests"]        # Les tests peuvent utiliser des patterns "dangereux"
```

---

## 6. Documentation auto-generee

### Comment ca marche

**Sphinx** avec l'extension **autodoc** lit les docstrings du code Python et genere une doc HTML automatiquement :

```python
# app/__init__.py
"""Flask CI/CD Demo application."""   # ← cette docstring apparait dans la doc
```

```rst
# docs/api.rst
.. automodule:: app
   :members:                          # ← genere la doc de tous les membres du module
```

### Theme Furo

Le site utilise le theme **Furo** qui offre :
- **Dark mode** automatique (suit les preferences systeme)
- Design moderne et responsive
- Navigation au clavier
- Lien GitHub dans le footer

### Pages de documentation

| Page | Format | Contenu |
|------|--------|---------|
| `index.rst` | RST | Page d'accueil, vue d'ensemble |
| `architecture.md` | Markdown | Strategie de branches, structure du projet, schema du CI |
| `api.rst` | RST | Reference API auto-generee depuis le code |
| `deployment.md` | Markdown | Guide de deploiement, Docker, workflow |

Le support Markdown est ajoute via **myst-parser** — ca permet de mixer RST (pour autodoc) et Markdown (pour le contenu redige).

### Deploiement de la doc

A chaque push sur `main`, la doc est buildee et deployee automatiquement sur **GitHub Pages** via le workflow `docs.yml`.

---

## 7. Docker

### Dockerfile

```dockerfile
FROM python:3.12-slim          # Image legere (~150MB vs ~900MB pour l'image complete)
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt   # --no-cache-dir = image plus petite
COPY . .
EXPOSE 5000
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "run:app"]
```

**Gunicorn** est le serveur WSGI de production (le serveur de dev Flask n'est pas fait pour la prod — un seul thread, pas de gestion de processus).

### Optimisations

- `python:3.12-slim` au lieu de `python:3.12` : image 5x plus petite
- `COPY requirements.txt` avant `COPY .` : le layer pip est cache tant que les deps ne changent pas (builds plus rapides)
- `--no-cache-dir` : pas de cache pip dans l'image finale

---

## 8. Securite

### Bandit

Bandit est un **analyseur statique de securite** pour Python. Il scan le code a la recherche de patterns dangereux :

- **B101** : utilisation de `assert` (desactive en prod)
- **B301** : utilisation de `pickle` (deserialization unsafe)
- **B608** : injection SQL
- **B602** : `subprocess` avec `shell=True`
- **B105** : mots de passe en dur

Dans le CI, Bandit genere un rapport JSON uploade comme artifact + un rapport lisible dans les logs.

### Bonnes pratiques implementees

- `SECRET_KEY` lue depuis l'environnement, pas en dur dans le code
- Validation des inputs (`title` requis dans POST /tasks)
- Codes de retour HTTP corrects (400, 404)
- Pas d'utilisation de `eval()`, `exec()`, ou `pickle`
- Tests dans un dossier separe exclu de l'analyse Bandit

---

## 9. Makefile

Le `Makefile` simplifie les commandes courantes :

```bash
make install     # Installe toutes les dependances
make run         # Lance l'app en local
make test        # Execute les tests avec couverture
make lint        # Verifie la qualite du code (black, isort, flake8, mypy)
make format      # Formate le code automatiquement (black + isort)
make security    # Lance l'analyse de securite Bandit
make docs        # Build la documentation Sphinx
make docs-serve  # Build + sert la doc sur localhost:8080
make clean       # Nettoie les fichiers generes
```

---

## 10. Fichiers complementaires

### `.gitignore`

Exclut du repo : `__pycache__/`, `.venv/`, `coverage.xml`, `.env`, fichiers de build.

### `.github/pull_request_template.md`

Template automatique pour les PRs avec une checklist :
- [ ] Tests passent localement
- [ ] Code formate
- [ ] Pas de problemes de securite
- [ ] Type checking OK

### `pyproject.toml`

Fichier de configuration centralise pour tous les outils Python (pytest, black, isort, mypy, bandit). Evite d'avoir un fichier de config par outil.

---

## Resume du flux complet

```
Developer push sur feature/x
         │
         ▼
    ┌─────────┐
    │   CI    │  Black + isort + Flake8 + Mypy
    │ Pipeline │  pytest (3.11 + 3.12) + coverage
    │         │  Bandit security scan
    └────┬────┘
         │ PR vers staging
         ▼
    ┌─────────┐
    │ Staging │  CI complet
    │ Deploy  │  Smoke test
    │         │  Deploy sur env staging
    └────┬────┘
         │ Merge staging → main
         ▼
    ┌─────────┐
    │  Prod   │  CI complet
    │ Deploy  │  Backup + Smoke test
    │         │  Deploy sur env production
    └────┬────┘
         │
         ▼
    ┌─────────┐
    │  Docs   │  Sphinx build
    │ Deploy  │  GitHub Pages
    └─────────┘
```
