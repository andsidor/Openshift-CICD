# Openshift-CICD

🇬🇧 [English](#english) | 🇵🇱 [Polski](#polski)

---

## English

Flask API returning stock prices (Yahoo Finance public endpoint, no API key) with a GitOps-style CI/CD flow:

GitHub push to `main` → webhook → OpenShift Pipelines (Tekton): clone → pytest → buildah build → deploy.

### Endpoints

- `GET /price/<symbol>` e.g. `/price/AAPL`
- `GET /healthz`

### Repository layout

| Path | Purpose |
|------|---------|
| `app/`, `tests/`, `requirements.txt`, `Dockerfile` | Application, tests and container image |
| `k8s/` | Kustomize-managed manifests (ImageStream, Deployment, Service, Route) |
| `tekton/pipeline.yaml` | Pipeline: clone → test → build → deploy |
| `tekton/trigger.yaml` | TriggerBinding, TriggerTemplate, EventListener and its Route |
| `tekton/cleanup.yaml` | Hourly CronJob that deletes old PipelineRuns (keeps the last 2) |

### Setup (namespace `asidor23-dev`)

```
oc apply -f tekton/pipeline.yaml -f tekton/trigger.yaml -f tekton/cleanup.yaml
oc create secret generic github-webhook-secret --from-literal=secret=<random>
```

Then add a GitHub webhook (content type `application/json`, event `push`) pointing to
`https://$(oc get route github-listener -o jsonpath='{.spec.host}')` with the same secret.

### GitOps

Git is the source of truth for the cluster state. The deploy step runs
`oc apply -k k8s/ --prune -l gitops=managed`, so every commit to `main` is applied
and resources removed from `k8s/` are pruned from the cluster
(Deployment, Service, Route, ImageStream).

Argo CD / Flux are not used: the OpenShift Developer Sandbox does not allow creating CRDs.

### Cleanup

The `pipelinerun-cleanup` CronJob runs every hour and keeps only the 2 newest PipelineRuns.
Deleting a PipelineRun also removes its pods and workspace PVC.

---

## Polski

API we Flasku zwracające ceny akcji (publiczny endpoint Yahoo Finance, bez klucza API) z przepływem CI/CD w stylu GitOps:

push na `main` w GitHubie → webhook → OpenShift Pipelines (Tekton): clone → pytest → budowanie buildah → deploy.

### Endpointy

- `GET /price/<symbol>` np. `/price/AAPL`
- `GET /healthz`

### Struktura repozytorium

| Ścieżka | Opis |
|---------|------|
| `app/`, `tests/`, `requirements.txt`, `Dockerfile` | Aplikacja, testy i obraz kontenera |
| `k8s/` | Manifesty zarządzane przez Kustomize (ImageStream, Deployment, Service, Route) |
| `tekton/pipeline.yaml` | Pipeline: clone → test → build → deploy |
| `tekton/trigger.yaml` | TriggerBinding, TriggerTemplate, EventListener i jego Route |
| `tekton/cleanup.yaml` | Co godzinę CronJob usuwa stare PipelineRuny (zostawia 2 ostatnie) |

### Instalacja (namespace `asidor23-dev`)

```
oc apply -f tekton/pipeline.yaml -f tekton/trigger.yaml -f tekton/cleanup.yaml
oc create secret generic github-webhook-secret --from-literal=secret=<losowy>
```

Następnie dodaj webhook w GitHubie (content type `application/json`, zdarzenie `push`) wskazujący na
`https://$(oc get route github-listener -o jsonpath='{.spec.host}')` z tym samym sekretem.

### GitOps

Git jest źródłem prawdy o stanie klastra. Krok deploy wykonuje
`oc apply -k k8s/ --prune -l gitops=managed`, więc każdy commit na `main` jest aplikowany,
a zasoby usunięte z `k8s/` znikają z klastra
(Deployment, Service, Route, ImageStream).

Nie używamy Argo CD ani Flux: OpenShift Developer Sandbox nie pozwala tworzyć CRD.

### Sprzątanie

CronJob `pipelinerun-cleanup` działa co godzinę i zostawia tylko 2 najnowsze PipelineRuny.
Usunięcie PipelineRuna usuwa też jego pody i PVC workspace'u.
