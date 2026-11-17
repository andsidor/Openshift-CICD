# Openshift-CICD

Flask API returning stock prices (Yahoo Finance public endpoint, no key) with a CI/CD flow:
GitHub push → webhook → OpenShift Pipelines (Tekton): clone → pytest → buildah build → deploy.

- `GET /price/<symbol>` e.g. `/price/AAPL`
- `GET /healthz`

Setup (namespace `asidor23-dev`):

```
oc apply -f tekton/pipeline.yaml -f tekton/trigger.yaml
oc create secret generic github-webhook-secret --from-literal=secret=<random>
```

Then add a GitHub webhook (content type `application/json`, event `push`) pointing to
`https://$(oc get route github-listener -o jsonpath='{.spec.host}')` with the same secret.
