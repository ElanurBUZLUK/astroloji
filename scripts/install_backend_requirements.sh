#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"

if ! command -v python >/dev/null 2>&1; then
  echo "[error] python is not available in PATH" >&2
  exit 1
fi

REQUIREMENTS_FILE="${PROJECT_ROOT}/backend/requirements.txt"
if [ ! -f "${REQUIREMENTS_FILE}" ]; then
  echo "[error] requirements file not found at ${REQUIREMENTS_FILE}" >&2
  exit 1
fi

echo "Installing backend dependencies from ${REQUIREMENTS_FILE}..."
python -m pip install --upgrade pip
python -m pip install -r "${REQUIREMENTS_FILE}"
echo "Done."
