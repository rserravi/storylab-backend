#!/usr/bin/env bash
set -euo pipefail

need() { command -v "$1" >/dev/null 2>&1 || { echo "Falta $1"; exit 1; }; }
need ollama

pull_if() {
  local name="$1"
  echo ">>> Pull: $name"
  if ollama pull "$name"; then
    echo "OK $name"
  else
    echo "WARN: no se pudo descargar $name"
  fi
}

# Modelos oficiales estables
pull_if "llama3.1:8b"
pull_if "qwen2.5:32b"

# Alternativas (descomenta si quieres más)
# pull_if "qwen2.5:7b"
# pull_if "llama3.2:3b"

# OpenHermes existe SIN tag 7b (si quieres probar, quita el comentario)
pull_if "openhermes"

# Mythomax no está en el registry oficial de Ollama; omitir

echo
echo "Modelos disponibles:"
ollama list
