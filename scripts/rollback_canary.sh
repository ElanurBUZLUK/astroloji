#!/usr/bin/env bash
set -euo pipefail

if [[ -z "${KUBECONFIG:-}" ]]; then
  echo "KUBECONFIG not set; skipping rollback." >&2
  exit 0
fi

if ! command -v kubectl >/dev/null 2>&1; then
  echo "kubectl not available; skipping rollback." >&2
  exit 0
fi

NAMESPACE="${K8S_NAMESPACE:-astro-prod}"
CANARY_NAME="${CANARY_RELEASE_NAME:-astro-backend-canary}"

echo "Rolling back canary deployment ${CANARY_NAME} in namespace ${NAMESPACE}" >&2
if ! kubectl rollout undo deployment/"${CANARY_NAME}" -n "${NAMESPACE}"; then
  echo "Rollback skipped: deployment ${CANARY_NAME} not found." >&2
fi
