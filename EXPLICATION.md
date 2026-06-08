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
| `GET` | `/` | Page d'accueil (HTML) | 200 |
| `GET` | `/health` | Health check | 200 |
| `GET` | `/api/tasks` | Lister les taches | 200 |
| `POST` | `/api/tasks` | Creer une tache | 201 / 400 |
| `PUT` | `/api/tasks/<id>` | Modifier une tache | 200 / 404 |
| `DELETE` | `/api/tasks/<id>` | Supprimer une tache | 200 / 404 |

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

Le projet utilise **un seul workflow unifie** (`pipeline.yml`) qui centralise tout : CI, deploy et documentation. Plus besoin de jongler entre plusieurs fichiers.

### Architecture

```
.github/
├── actions/
│   └── setup-python/
│       └── action.yml        → Action composite reutilisable
└── workflows/
    └── pipeline.yml          → Pipeline unique
```

### Action composite (`setup-python`)

Pour eviter de repeter le setup Python + install des dependances dans chaque job, une **action composite** factorise ces steps :

```yaml
# .github/actions/setup-python/action.yml
inputs:
  python-version:
    default: "3.12"

runs:
  using: composite
  steps:
    - name: Set up Python
      uses: actions/setup-python@v5
      with:
        python-version: ${{ inputs.python-version }}
        cache: "pip"

    - name: Install dependencies
      shell: bash
      run: pip install -r requirements-dev.txt
```

Chaque job n'a plus qu'a faire :
```yaml
- uses: actions/checkout@v4
- uses: ./.github/actions/setup-python
```

### Declencheur

**Push ou PR** sur `main` et `staging` — un seul trigger pour tout.

### Jobs CI (en parallele)

La pipeline execute **5 jobs en parallele** :

#### Job 1 : Code Quality (lint)

Verifie la qualite du code sans l'executer :

| Outil | Role | Ce qu'il verifie |
|-------|------|-----------------|
| **Black** | Formateur | Le code est-il formate selon le standard Black ? (ligne max 88 car.) |
| **isort** | Tri des imports | Les imports sont-ils tries et groupes correctement ? |
| **Flake8** | Linter | Erreurs de style PEP8, variables inutilisees, imports manquants |
| **Mypy** | Type checker | Les annotations de type sont-elles coherentes ? |

#### Job 2 : Tests

Execute les tests sur **2 versions de Python** (3.11 et 3.12) grace a une **matrix strategy** :

```yaml
strategy:
  matrix:
    python-version: ["3.11", "3.12"]
```

Cela cree 2 jobs paralleles, un par version. Si les tests passent sur 3.11 mais echouent sur 3.12 (ou l'inverse), on le voit immediatement.

Les tests sont executes avec **pytest** et generent un **rapport de couverture** (coverage). Le rapport est uploade comme **artifact** GitHub Actions (telechargeable depuis l'interface).

#### Job 3 : Security Scan

**Bandit** analyse statiquement le code Python pour detecter des failles de securite courantes :

- Utilisation de `eval()` ou `exec()`
- Requetes HTTP sans verification SSL
- Mots de passe en dur
- Injections SQL
- Utilisation de fonctions dangereuses

Le rapport JSON est aussi uploade comme artifact.

#### Job 4 : Trivy Container Scan

**Trivy** complete Bandit en scannant l'**image Docker** plutot que le code source. Il detecte :

- CVE connues dans les packages pip (ex: une version de Flask ou Werkzeug vulnerable)
- Vulnerabilites dans les librairies systeme de l'image Docker (`python:3.12-slim`)
- Mauvaises configurations du Dockerfile

Le job build l'image Docker puis la scanne pour les vulnerabilites **CRITICAL** et **HIGH**. Le scan genere un rapport **JSON**, puis une etape de **gate fait echouer le job** si au moins une vulnerabilite est trouvee — une CVE dans une dependance **bloque donc le merge et le deploy**. L'option `ignore-unfixed: true` limite le blocage aux CVE **corrigeables** (celles sans patch disponible n'arretent pas la pipeline).

Le detail des CVE (package, version, severite, CVE, version corrigee) est repris dans le **Pipeline Report** (voir Job 6), pas seulement dans les logs.

> Note : `safety` (l'equivalent de `npm audit` pour `requirements.txt`) n'est volontairement pas utilise — la couverture CVE des dependances est deja assuree par Trivy (scan de l'image) et **Dependabot**.

#### Job 5 : Documentation

**Build** la documentation Sphinx a partir du code source et l'uploade comme artifact.

```yaml
- name: Build Sphinx documentation
  run: sphinx-build -b html docs/ docs/_build/html -W   # -W = warnings = erreurs
```

Le flag `-W` fait echouer le build si la doc contient des warnings — ca force a maintenir une doc propre.

#### Job 6 : Pipeline Report

Ce job tourne **apres** les 5 autres (`needs: [...]`, `if: always()`) et **agrege** tous les resultats dans le **step summary** de GitHub Actions (`$GITHUB_STEP_SUMMARY`), visible sur la page du run (onglet *Summary*, pas dans les logs) :

- un tableau recapitulatif du statut de chaque job (✅/❌) ;
- la **couverture de tests** (lue depuis `coverage.xml`) ;
- le nombre de findings **Bandit** ;
- le **detail des CVE Trivy** (package, version, severite, CVE, version corrigee), via le script `.github/scripts/trivy_summary.py`.

Une derniere etape fait **echouer la pipeline** si l'un des jobs requis a echoue — le report reste donc toujours genere (meme en cas d'echec), ce qui permet de voir *pourquoi* ca a casse.

### Jobs de deploiement (conditionnels)

Les jobs de deploy **attendent que les 4 jobs CI passent** (`needs: [lint, test, security, trivy]`) et ne s'executent que sur les push (pas les PR) :

| Job | Condition | Environnement | Action |
|-----|-----------|---------------|--------|
| **deploy-staging** | Push sur `staging` | `staging` | Webhook Coolify staging |
| **deploy-production** | Push sur `main` | `production` | Webhook Coolify production |

```yaml
deploy-production:
  needs: [lint, test, security, trivy]
  if: github.event_name == 'push' && github.ref == 'refs/heads/main'
  environment: production
```

Le deploiement se fait via un **webhook Coolify** — un simple appel HTTP authentifie qui declenche le redeploy cote serveur. Les secrets (`COOLIFY_API_TOKEN`, `COOLIFY_PROD_WEBHOOK`, `COOLIFY_WEBHOOK_STAGING`) sont stockes dans les environments GitHub.

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

**12 tests** couvrant **95% du code** :

- **Config** (3 tests) : verifie que chaque environnement a les bons flags (`DEBUG`, `TESTING`)
- **Routes** (9 tests) : teste chaque endpoint avec les cas normaux ET les cas d'erreur (404, 400)

Exemples :
```python
def test_create_task(client):
    response = client.post("/api/tasks", data=json.dumps({"title": "Test"}), ...)
    assert response.status_code == 201

def test_create_task_missing_title(client):      # ← cas d'erreur
    response = client.post("/api/tasks", data=json.dumps({}), ...)
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

### Approche : deux couches

La doc est generee a **deux niveaux**, tous deux directement depuis le code :

1. **Reference HTTP** (page `api`) — generee depuis la table de routage Flask par **`sphinxcontrib-httpdomain`** (directive `autoflask`). Elle lit directement les routes : methode, chemin, parametres et codes de statut. Une API REST est ainsi documentee *comme* une API REST, et non comme une simple liste de fonctions Python.

2. **Internals Python** (page `internals`) — la factory `create_app` et les classes de config sont documentees avec l'**autodoc** classique de Sphinx (ce sont de vrais objets Python).

```rst
# docs/api.rst
.. qrefflask:: app:create_app()      # table de synthese des endpoints
   :undoc-static:

.. autoflask:: app:create_app()      # reference detaillee, lue depuis les routes
   :undoc-static:
   :order: path
```

La table de synthese est alimentee par les tags `.. :quickref:` places dans les docstrings de chaque route :

```python
@api.route("/api/tasks", methods=["POST"])
def create_task():
    """Create a new task.

    .. :quickref: Tasks; Create a new task   # ← regroupe et resume l'endpoint
    ...
    """
```

### Theme Furo + style personnalise

Le site utilise le theme **Furo** (dark mode automatique, responsive, navigation clavier, lien GitHub en footer). Un fichier **`docs/_static/custom.css`** transforme la sortie brute de httpdomain en style type "Stripe/Redoc" :

- chaque endpoint est une **carte** avec une bordure laterale coloree
- chaque methode HTTP a un **badge colore** (GET bleu, POST vert, PUT orange, DELETE rouge)
- les codes de statut (`201 Created`, `404 Not Found`) sont rendus en mini-badges

### Pages de documentation

| Page | Format | Contenu |
|------|--------|---------|
| `index.rst` | RST | Page d'accueil, vue d'ensemble |
| `quickstart.rst` | RST | Installation + exemples `curl` par endpoint |
| `api.rst` | RST | Reference HTTP auto-generee (httpdomain) |
| `internals.rst` | RST | Factory `create_app` + classes de config (autodoc) |

### Construction et publication

- En **CI** : le job `docs` build la doc avec `sphinx-build -b html docs/ ... -W` (le `-W` fait echouer le build au moindre warning) et l'uploade comme artifact.
- Dans le **Docker** : la doc est buildee pendant le build de l'image et embarquee ; l'application la sert directement sur la route **`/docs/`**.

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
    ┌──────────────────────────────────────────┐
    │            pipeline.yml                  │
    │                                          │
    │  ┌──────┐ ┌──────┐ ┌────────┐ ┌─────┐ ┌────┐ │
    │  │ Lint │ │ Test │ │Security│ │Trivy│ │Docs│ │ ← En parallele
    │  └──┬───┘ └──┬───┘ └───┬────┘ └──┬──┘ └────┘ │
    │     │        │         │         │            │
    │     └────────┼─────────┼─────────┘            │
    │              │         │                      │
    │    needs: [lint, test, security, trivy]        │
    │               │                          │
    │     ┌─────────┴──────────┐               │
    │     │                    │               │
    │  ┌──▼──────┐   ┌────────▼─┐             │
    │  │ Deploy  │   │  Deploy  │             │  ← Conditionnel
    │  │ Staging │   │   Prod   │             │
    │  └─────────┘   └──────────┘             │
    │  if: staging     if: main               │
    └──────────────────────────────────────────┘
```

---

## 11. Securite : Bandit + Trivy

Le projet utilise **deux outils de securite complementaires** :

| Outil | Ce qu'il scanne | Ce qu'il detecte |
|-------|----------------|-----------------|
| **Bandit** | Code source Python | Patterns dangereux (`eval`, `exec`, mots de passe en dur, injections) |
| **Trivy** | Image Docker complete | CVE dans les packages pip, vulnerabilites OS de l'image, misconfigurations Dockerfile |

Bandit seul ne suffit pas : le code peut etre propre mais embarquer une dependance avec une CVE critique. Trivy comble ce manque en scannant le container build avec les severites **CRITICAL** et **HIGH**.
