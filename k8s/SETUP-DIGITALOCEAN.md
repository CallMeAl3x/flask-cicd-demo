# Setup DigitalOcean Kubernetes (DOKS)

Guide pas à pas pour créer le cluster Kubernetes managé qui héberge l'API Flask.
À faire **une seule fois**. Pendant ce temps, le code (manifests + CI) est préparé en parallèle.

> **Coût** : le control plane DOKS est **gratuit**. Tu paies seulement le node (~12 $/mois) et le
> LoadBalancer (~12 $/mois). Un nouveau compte reçoit **200 $ de crédit valables 60 jours** → tout est
> couvert. Pense à **supprimer le cluster** après la soutenance pour ne rien consommer inutilement
> (voir [§7](#7-nettoyage-après-la-soutenance)).

---

## 1. Créer le compte et activer le crédit

1. Va sur <https://www.digitalocean.com/> → **Sign up** (GitHub ou email).
2. Ajoute une carte bancaire (obligatoire pour débloquer le crédit ; non débitée tant que tu restes
   sous 200 $).
3. Vérifie le crédit dans **Billing** → tu dois voir « $200 in credits ».

---

## 2. Installer et authentifier `doctl` (CLI DigitalOcean)

`doctl` est la CLI officielle DigitalOcean.

**macOS (Homebrew)** :
```bash
brew install doctl
```

**Linux** :
```bash
cd /tmp
curl -sL https://github.com/digitalocean/doctl/releases/latest/download/doctl-$(uname -s)-amd64.tar.gz | tar xz
sudo mv doctl /usr/local/bin
```

**Créer un token API** :
1. Dans le dashboard DO : **API** (menu de gauche) → **Generate New Token**.
2. Nom : `flask-cicd`, scopes : **Read + Write**, expiration : 90 jours (ou plus).
3. **Copie le token immédiatement** (affiché une seule fois).

**Authentifier la CLI** :
```bash
doctl auth init        # colle le token quand demandé
doctl account get      # doit afficher ton compte → l'auth fonctionne
```

> 🔐 Garde ce token de côté : il servira aussi de **secret GitHub** (étape 5) pour que la CI déploie.

---

## 3. Vérifier que `kubectl` est installé

```bash
kubectl version --client    # si absent : brew install kubectl  (ou voir kubernetes.io/docs/tasks/tools)
```

---

## 4. Créer le cluster Kubernetes

```bash
doctl kubernetes cluster create flask-cluster \
  --region fra1 \
  --node-pool "name=pool;size=s-1vcpu-2gb;count=1" \
  --wait
```

- `flask-cluster` : **garde ce nom exact** — la CI s'en sert pour récupérer le kubeconfig.
- `--region fra1` : Francfort (proche de la France ; voir `doctl kubernetes options regions` pour la liste).
- `s-1vcpu-2gb` : le plus petit node, suffisant pour cette app.
- `--wait` : attend que le cluster soit prêt (~4-5 min).

À la fin, `doctl` configure automatiquement `kubectl` pour pointer sur le nouveau cluster.

**Vérifier** :
```bash
kubectl get nodes      # doit lister 1 node en STATUS "Ready"
```

Si jamais le contexte kubectl n'est pas configuré :
```bash
doctl kubernetes cluster kubeconfig save flask-cluster
```

---

## 5. Ajouter le secret GitHub pour le déploiement automatique

La CI régénère le kubeconfig à chaque run avec `doctl` (plus robuste qu'un kubeconfig statique qui expire).
Il suffit donc d'exposer le **token API** comme secret.

1. Sur GitHub : repo **`CallMeAl3x/flask-cicd-demo`** → **Settings** → **Secrets and variables** →
   **Actions** → **New repository secret**.
2. Name : `DIGITALOCEAN_ACCESS_TOKEN`
3. Value : le token API DO de l'étape 2.
4. **Add secret**.

> Pas besoin de secret pour GHCR : le `GITHUB_TOKEN` intégré suffit à pousser l'image dans le registry
> du repo.

---

## 5b. Rendre l'image GHCR publique (une seule fois, après le 1er push)

Par défaut, l'image poussée sur GHCR est **privée** → le cluster DigitalOcean ne pourra pas la tirer
(`ImagePullBackOff`). Le plus simple est de rendre le package public :

1. Après le premier run de la CI (job `build-push`), va sur le repo GitHub → onglet de droite
   **Packages** → clique sur `flask-cicd-demo`.
2. **Package settings** (⚙️) → section **Danger Zone** → **Change visibility** → **Public** → confirme.

> Alternative (si tu veux garder l'image privée) : créer un `imagePullSecret` dans le cluster avec un
> Personal Access Token GitHub (`read:packages`) et le référencer dans le `deployment.yaml`. Préviens-moi
> si tu préfères cette option, je l'ajoute.

---

## 6. Vérifier l'accès public (après le premier déploiement)

Une fois que la CI a tourné (ou après un `kubectl apply -k k8s/` manuel), DigitalOcean provisionne un
**LoadBalancer** avec une IP publique :

```bash
kubectl get svc flask-app        # attends que EXTERNAL-IP passe de <pending> à une vraie IP (~1-2 min)
curl http://<EXTERNAL-IP>/health # doit renvoyer {"status":"healthy"}
```

Cette IP est la **preuve vérifiable** que l'app tourne sur Kubernetes.

---

## 7. Nettoyage (après la soutenance)

Pour ne plus rien consommer du crédit :
```bash
doctl kubernetes cluster delete flask-cluster
```
Cela supprime le node **et** le LoadBalancer associé.

---

## Récapitulatif des valeurs à retenir

| Élément | Valeur |
|---|---|
| Nom du cluster | `flask-cluster` |
| Région | `fra1` |
| Secret GitHub | `DIGITALOCEAN_ACCESS_TOKEN` |
| Image GHCR | `ghcr.io/callmeal3x/flask-cicd-demo` |
| Endpoint de test | `http://<EXTERNAL-IP>/health` |

> Si tu changes le nom du cluster ou la région, préviens-moi : ces valeurs sont aussi codées dans le job
> `deploy-k8s` du pipeline et dans `k8s/`.
