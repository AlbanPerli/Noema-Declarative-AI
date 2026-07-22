#!/usr/bin/env bash
set -euo pipefail

PROJECT_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PYTHON_BIN="${NOEMA_METAL_PYTHON:-/opt/homebrew/bin/python3.13}"
VENV_DIR="${NOEMA_METAL_VENV:-${PROJECT_ROOT}/.venv-metal}"

if [ ! -x "${PYTHON_BIN}" ]; then
  echo "Python runtime not found: ${PYTHON_BIN}" >&2
  echo "Install Homebrew python@3.13 or set NOEMA_METAL_PYTHON=/path/to/python." >&2
  exit 1
fi

"${PYTHON_BIN}" -m venv "${VENV_DIR}"
"${VENV_DIR}/bin/python" -m pip install --upgrade pip setuptools wheel

cd "${PROJECT_ROOT}"
CMAKE_ARGS="-DGGML_METAL=on -DGGML_NATIVE=on" \
FORCE_CMAKE=1 \
"${VENV_DIR}/bin/python" -m pip install --force-reinstall -e .

"${VENV_DIR}/bin/python" -m pip install pytest

echo "Metal runtime ready: ${VENV_DIR}/bin/python"
