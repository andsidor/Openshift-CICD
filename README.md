# Openshift-CICD

🇬🇧 [English](#english) | 🇵🇱 [Polski](#polski)

---

## English

### About the project

This project is a demo of a complete CI/CD pipeline on the OpenShift Developer Sandbox. A small Flask service returns current stock prices from a public API. Every push to `main` on GitHub triggers a Tekton pipeline that tests the code, builds a container image and deploys it to OpenShift with no manual steps. Kubernetes manifests live in Git and are applied with Kustomize, so the repository always describes the state of the cluster. Old pipeline runs are cleaned up automatically.

Flask API returning stock prices (Yahoo Finance public endpoint, no API key) with a GitOps-style CI/CD flow:

GitHub push to `main` → webhook → OpenShift Pipelines (Tekton): clone → pytest + security scan (bandit, pip-audit) → buildah build → Trivy image scan → image tag + deploy.

### Architecture

```mermaid
flowchart LR
    Dev[Developer] -->|git push main| GH[GitHub]
    GH -->|webhook| EL[EventListener]
    EL --> C
    subgraph Tekton[OpenShift Pipelines]
        direction LR
        C[clone] --> T[test]
        C --> S["security-scan<br/>bandit, pip-audit"]
        T --> B["build<br/>buildah"]
        S --> B
        B --> I["image-scan<br/>Trivy"]
        I --> TG[tag-image]
        I --> D["deploy<br/>oc apply -k"]
    end
    B -->|push| REG[("ImageStream<br/>stock-api")]
    TG -->|tag sha| REG
    D --> APP["Deployment + Service + Route"]
    REG --> APP
    CM["k8s/stocks.txt<br/>ConfigMap"] --> APP
    APP -->|/prices| Y[Yahoo Finance]
```

### Endpoints

- `GET /price/<symbol>` e.g. `/price/AAPL`
- `GET /prices` prices for all symbols from `k8s/stocks.txt`
- `GET /stocks` list of configured symbols
- `GET /healthz`

### Stock list

Symbols are read from the external file [k8s/stocks.txt](k8s/stocks.txt) (one per line, `#` comments allowed). Kustomize turns it into a ConfigMap mounted at `/config/stocks.txt`; edit the file and push to `main` to change the list - the pipeline redeploys automatically.

### Repository layout

| Path | Purpose |
|------|---------|
| `app/`, `tests/`, `requirements.txt`, `Dockerfile` | Application, tests and container image |
| `k8s/` | Kustomize-managed manifests (ImageStream, Deployment, Service, Route) |
| `tekton/pipeline.yaml` | Pipeline: clone → test + security-scan → build → image-scan → tag-image + deploy |
| `tekton/pipeline-pr.yaml` | CI-only pipeline for Pull Requests: clone → test + security-scan |
| `tekton/trigger.yaml` | TriggerBinding, TriggerTemplate, EventListener and its Route |
| `tekton/cleanup.yaml` | Hourly CronJob that deletes old PipelineRuns (keeps the last 2) |

### Setup (namespace `asidor23-dev`)

```
oc apply -f tekton/pipeline.yaml -f tekton/pipeline-pr.yaml -f tekton/trigger.yaml -f tekton/cleanup.yaml
oc create secret generic github-webhook-secret --from-literal=secret=<random>
```

Then add a GitHub webhook (content type `application/json`, event `push`) pointing to
`https://$(oc get route github-listener -o jsonpath='{.spec.host}')` with the same secret.

### GitOps

Git is the source of truth for the cluster state. The deploy step runs
`oc apply -k k8s/ --prune -l gitops=managed`, so every commit to `main` is applied
and resources removed from `k8s/` are pruned from the cluster
(Deployment, Service, Route, ImageStream, ConfigMap).

Argo CD / Flux are not used: the OpenShift Developer Sandbox does not allow creating CRDs.

### Security scanning

The `security-scan` task runs in parallel with the tests and blocks the build on findings: `bandit` (static analysis of `app/`, medium+ severity) and `pip-audit` (known vulnerabilities in `requirements.txt`).

### Image scan & registry

After `build`, Trivy scans the image (HIGH/CRITICAL, fixable only) and fails the pipeline on findings. The `Dockerfile` updates OS packages and `setuptools`. Passing images are tagged in the internal OpenShift registry as `stock-api:latest` and `stock-api:<git-commit-sha>` (`oc get is stock-api`). The `krb5-libs` CVEs (fix only in RHEL 9.9) are explicitly accepted in `tekton/pipeline.yaml`.

### Pull Request CI & rollback

- Pull requests (`opened`, `synchronize`, `reopened`) trigger the lightweight `stock-api-ci-pipeline` ([tekton/pipeline-pr.yaml](tekton/pipeline-pr.yaml)): clone → pytest + security scan. No image build, no deployment. The webhook sends both `push` and `pull_request` events.
- After `oc apply -k`, the deploy step waits for `oc rollout status` (60 s). On failure it runs `oc rollout undo deployment/stock-api` and fails the pipeline. The Deployment uses the immutable `stock-api:<git-commit-sha>` image (deploy runs after `tag-image`), so the undo restores exactly the previous container image.

### Cleanup

The `pipelinerun-cleanup` CronJob runs every hour and keeps only the 2 newest PipelineRuns.
Deleting a PipelineRun also removes its pods and workspace PVC.

---

## Polski

### O projekcie

Projekt to demonstracja kompletnego procesu CI/CD na OpenShift Developer Sandbox. Mała usługa we Flasku zwraca aktualne ceny akcji z publicznego API. Każdy push na `main` w GitHubie uruchamia pipeline Tekton, który testuje kod, buduje obraz kontenera i wdraża go na OpenShift bez ręcznych kroków. Manifesty Kubernetes są w Gicie i aplikowane przez Kustomize, więc repozytorium zawsze opisuje stan klastra. Stare przebiegi pipeline'u są sprzątane automatycznie.

API we Flasku zwracające ceny akcji (publiczny endpoint Yahoo Finance, bez klucza API) z przepływem CI/CD w stylu GitOps:

push na `main` w GitHubie → webhook → OpenShift Pipelines (Tekton): clone → pytest + skan bezpieczeństwa (bandit, pip-audit) → budowanie buildah → skan obrazu Trivy → tag obrazu + deploy.

### Architektura

```mermaid
flowchart LR
    Dev[Developer] -->|git push main| GH[GitHub]
    GH -->|webhook| EL[EventListener]
    EL --> C
    subgraph Tekton[OpenShift Pipelines]
        direction LR
        C[clone] --> T[test]
        C --> S["security-scan<br/>bandit, pip-audit"]
        T --> B["build<br/>buildah"]
        S --> B
        B --> I["image-scan<br/>Trivy"]
        I --> TG[tag-image]
        I --> D["deploy<br/>oc apply -k"]
    end
    B -->|push| REG[("ImageStream<br/>stock-api")]
    TG -->|tag sha| REG
    D --> APP["Deployment + Service + Route"]
    REG --> APP
    CM["k8s/stocks.txt<br/>ConfigMap"] --> APP
    APP -->|/prices| Y[Yahoo Finance]
```

### Endpointy

- `GET /price/<symbol>` np. `/price/AAPL`
- `GET /prices` ceny wszystkich symboli z `k8s/stocks.txt`
- `GET /stocks` lista skonfigurowanych symboli
- `GET /healthz`

### Lista akcji

Symbole są czytane z zewnętrznego pliku [k8s/stocks.txt](k8s/stocks.txt) (jeden w linii, komentarze `#` dozwolone). Kustomize zamienia go na ConfigMap montowany w `/config/stocks.txt`; zmień plik i zrób push na `main`, a pipeline sam wdroży nową listę.

### Struktura repozytorium

| Ścieżka | Opis |
|---------|------|
| `app/`, `tests/`, `requirements.txt`, `Dockerfile` | Aplikacja, testy i obraz kontenera |
| `k8s/` | Manifesty zarządzane przez Kustomize (ImageStream, Deployment, Service, Route) |
| `tekton/pipeline.yaml` | Pipeline: clone → test + security-scan → build → image-scan → tag-image + deploy |
| `tekton/pipeline-pr.yaml` | Pipeline CI dla Pull Requestów: clone → test + security-scan |
| `tekton/trigger.yaml` | TriggerBinding, TriggerTemplate, EventListener i jego Route |
| `tekton/cleanup.yaml` | Co godzinę CronJob usuwa stare PipelineRuny (zostawia 2 ostatnie) |

### Instalacja (namespace `asidor23-dev`)

```
oc apply -f tekton/pipeline.yaml -f tekton/pipeline-pr.yaml -f tekton/trigger.yaml -f tekton/cleanup.yaml
oc create secret generic github-webhook-secret --from-literal=secret=<losowy>
```

Następnie dodaj webhook w GitHubie (content type `application/json`, zdarzenie `push`) wskazujący na
`https://$(oc get route github-listener -o jsonpath='{.spec.host}')` z tym samym sekretem.

### GitOps

Git jest źródłem prawdy o stanie klastra. Krok deploy wykonuje
`oc apply -k k8s/ --prune -l gitops=managed`, więc każdy commit na `main` jest aplikowany,
a zasoby usunięte z `k8s/` znikają z klastra
(Deployment, Service, Route, ImageStream, ConfigMap).

Nie używamy Argo CD ani Flux: OpenShift Developer Sandbox nie pozwala tworzyć CRD.

### Skanowanie bezpieczeństwa

Zadanie `security-scan` działa równolegle z testami i blokuje build przy znaleziskach: `bandit` (analiza statyczna `app/`, poziom medium i wyżej) oraz `pip-audit` (znane podatności w `requirements.txt`).

### Skan obrazu i rejestr

Po `build` Trivy skanuje obraz (HIGH/CRITICAL, tylko z poprawką) i przerywa pipeline przy znaleziskach. `Dockerfile` aktualizuje pakiety systemowe i `setuptools`. Obrazy po skanie są tagowane w wewnętrznym rejestrze OpenShift jako `stock-api:latest` i `stock-api:<sha-commitu>` (`oc get is stock-api`). CVE `krb5-libs` (poprawka tylko w RHEL 9.9) są świadomie zaakceptowane w `tekton/pipeline.yaml`.

### Pull Request CI i rollback

- Pull requesty (`opened`, `synchronize`, `reopened`) uruchamiają lekki pipeline `stock-api-ci-pipeline` ([tekton/pipeline-pr.yaml](tekton/pipeline-pr.yaml)): clone → pytest + skan bezpieczeństwa. Bez budowania obrazu i wdrożenia. Webhook wysyła zdarzenia `push` i `pull_request`.
- Po `oc apply -k` krok deploy czeka na `oc rollout status` (60 s). Przy błędzie wykonuje `oc rollout undo deployment/stock-api` i kończy pipeline porażką. Deployment używa niezmiennego obrazu `stock-api:<sha-commitu>` (deploy działa po `tag-image`), więc undo przywraca dokładnie poprzedni obraz kontenera.

### Sprzątanie

CronJob `pipelinerun-cleanup` działa co godzinę i zostawia tylko 2 najnowsze PipelineRuny.
Usunięcie PipelineRuna usuwa też jego pody i PVC workspace'u.


---

## Screenshots / Zrzuty ekranu

Widoki z OpenShift Developer Sandbox (namespace `asidor23-dev`) pokazujące działające środowisko. / Views from the OpenShift Developer Sandbox showing the running environment.

### Cluster overview / Przegląd klastra

| Screenshot | Comment |
|---|---|
| ![Projects](_files/Projects.png) | Projects: namespace `asidor23-dev` in the sandbox / projekt w sandboxie |
| ![Topology](_files/Topology.png) | Topology: the `stock-api` application / topologia aplikacji |
| ![Pods](_files/Pods.png) | Pods: running app and pipeline pods / działające pody aplikacji i pipeline'u |
| ![Events](_files/Events.png) | Events: cluster events from deployments and pipeline runs / zdarzenia z wdrożeń i przebiegów |

### Workloads and configuration / Obciążenia i konfiguracja

| Screenshot | Comment |
|---|---|
| ![Deployments](_files/Deployments.png) | Deployment `stock-api` managed by Kustomize / Deployment zarządzany przez Kustomize |
| ![Services](_files/Services.png) | Service exposing the app on port 8080 / Service wystawiający aplikację |
| ![ConfigMap](_files/ConfigMap.png) | ConfigMap generated from `k8s/stocks.txt` (stock list) / ConfigMap z listą akcji |
| ![Secrets](_files/Secrests.png) | Secrets, incl. the GitHub webhook secret / sekrety, w tym webhook GitHub |
| ![CronJobs](_files/CronJobs.png) | CronJob `pipelinerun-cleanup`, hourly cleanup / godzinne sprzątanie |
| ![PVC](_files/PVC.png) | PVCs used as pipeline workspaces / PVC jako workspace pipeline'u |
| ![NetworkPolicy](_files/NetworkPolicy.png) | NetworkPolicies in the namespace / polityki sieciowe |
| ![API](_files/API.png) | Application API response (`/prices`) / odpowiedź API aplikacji |

### CI/CD (Tekton)

| Screenshot | Comment |
|---|---|
| ![Pipeline overview](_files/Pipeline_overview.png) | Pipeline runs overview / przegląd przebiegów |
| ![Pipeline](_files/Pipeline.png) | Pipeline: clone → test + security-scan → build → image-scan → tag-image + deploy |
| ![Triggers](_files/Triggers.png) | Triggers: EventListener fired by the GitHub push webhook / wyzwalanie z webhooka GitHub |

### Access control / Uprawnienia

| Screenshot | Comment |
|---|---|
| ![Service account](_files/Service_account.png) | Service account used by the pipeline / konto serwisowe pipeline'u |
| ![Role](_files/Role.png) | Role allowing cleanup of PipelineRuns / rola do sprzątania |
| ![Role binding](_files/Role_binding.png) | RoleBinding for the cleanup role / powiązanie roli |

### Project / Projekt

| Screenshot | Comment |
|---|---|
| ![Project overview](_files/Project_overview.png) | Project overview / przegląd projektu |
| ![Project details](_files/Project_details.png) | Project details / szczegóły projektu |
| ![Project RoleBinding](_files/Project_RoleBinding.png) | Project role bindings / powiązania ról w projekcie |

### Monitoring / Monitoring

| Screenshot | Comment |
|---|---|
| ![Dashboard](_files/Dashboard.png) | Dashboard overview / ogólny dashboard |
| ![Dashboard 2](_files/Dashboard_2.png) | Dashboard, additional view / dodatkowy widok |
| ![CPU](_files/Dashboard_CPU.png) | CPU usage / zużycie CPU |
| ![Memory](_files/Dashboard_Memory.png) | Memory usage / zużycie pamięci |
| ![Network](_files/Dasboard_network.png) | Network traffic / ruch sieciowy |
| ![Storage](_files/Dasboard_storage.png) | Storage usage / zużycie dysku |
