#!/usr/bin/env bash
set -euo pipefail

# 1) API viva
curl -fsS http://localhost:8080/health | jq .

# 2) Modelos disponibles en Ollama
curl -fsS http://localhost:11434/api/tags | jq '.models | map(.name)'

# 3) Probar generación mínima con el default
curl -fsS http://localhost:11434/api/generate \
  -H "Content-Type: application/json" \
  -d '{"model":"llama3.1:8b","prompt":"Di: listo.","stream":false}' | jq '.response'
