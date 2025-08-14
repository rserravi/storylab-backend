#!/usr/bin/env bash
set -euo pipefail

# Requiere Ollama instalado y servicio corriendo (ollama serve)
# Modelos de texto
ollama pull llama3.1:8b
ollama pull qwen2.5:32b || echo "WARN: qwen2.5:32b no disponible o requiere HW alto."
ollama pull openhermes:7b || echo "WARN: openhermes:7b no disponible."
ollama pull mythomax:13b || echo "WARN: mythomax:13b no disponible."

echo "Modelos listados:"
ollama list
