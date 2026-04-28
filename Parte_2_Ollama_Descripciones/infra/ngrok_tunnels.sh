#!/usr/bin/env bash
# Levanta DOS túneles ngrok simultáneos: Ollama (:11434) y generador (:8000).
# Requiere ngrok configurado con auth-token (ngrok config add-authtoken ...).

set -euo pipefail

# ngrok soporta múltiples túneles simultáneos vía archivo de config.
NGROK_CONFIG="${NGROK_CONFIG:-/home/ec2-user/SageMaker/ngrok.yml}"

if [[ ! -f "$NGROK_CONFIG" ]]; then
  cat > "$NGROK_CONFIG" <<EOF
version: "3"
agent:
  authtoken: ${NGROK_AUTHTOKEN:?Define NGROK_AUTHTOKEN antes de correr este script}
tunnels:
  ollama:
    proto: http
    addr: 11434
  generator:
    proto: http
    addr: 8000
EOF
  echo "→ ngrok.yml creado en $NGROK_CONFIG"
fi

echo "→ levantando túneles (Ctrl-C para detener; corre en foreground o usa nohup)"
ngrok start --all --config "$NGROK_CONFIG"
