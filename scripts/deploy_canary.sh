#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${KUBECONFIG:-}" ]]; then
  echo "KUBECONFIG not set; skipping canary deployment." >&2
  exit 0
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl not available; skipping canary deployment." >&2
  exit 0
fi

NAMESPACE="${K8S_NAMESPACE:-astro-prod}"
CANARY_NAME="${CANARY_RELEASE_NAME:-astro-backend-canary}"
CANARY_IMAGE="${CANARY_IMAGE:-ghcr.io/example/astro-backend:canary}"

echo "Deploying canary ${CANARY_NAME} into namespace ${NAMESPACE} with image ${CANARY_IMAGE}" >&2

if [[ -f infra/k8s/backend-deployment.yaml ]]; then
  kubectl apply -n "${NAMESPACE}" -f infra/k8s/backend-deployment.yaml
fi

if [[ -f infra/k8s/backend-service.yaml ]]; then
  kubectl apply -n "${NAMESPACE}" -f infra/k8s/backend-service.yaml
fi

if [[ -f infra/k8s/backend-canary.yaml ]]; then
  sed \
    -e "s#__CANARY_IMAGE__#${CANARY_IMAGE}#g" \
    -e "s#__CANARY_NAME__#${CANARY_NAME}#g" \
    infra/k8s/backend-canary.yaml | kubectl apply -n "${NAMESPACE}" -f -
else
  echo "Canary manifest infra/k8s/backend-canary.yaml not found; nothing to deploy." >&2
  exit 0
fi

kubectl rollout status deployment/"${CANARY_NAME}" -n "${NAMESPACE}" --timeout=180s
echo "Canary deployment ${CANARY_NAME} ready." >&2
