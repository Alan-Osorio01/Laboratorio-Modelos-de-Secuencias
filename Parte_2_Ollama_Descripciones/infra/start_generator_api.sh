#!/usr/bin/env bash
# Levanta el FastAPI del generador en SageMaker (puerto 8000).
# Lee el checkpoint desde /home/ec2-user/SageMaker/models/best_model.pt.

set -euo pipefail

REPO_ROOT="${REPO_ROOT:-/home/ec2-user/SageMaker/Laboratorio-Modelos-de-Secuencias}"
PORT="${PORT:-8000}"

cd "$REPO_ROOT"

export CHECKPOINT="${CHECKPOINT:-/home/ec2-user/SageMaker/models/best_model.pt}"
export DATA_CSV="${DATA_CSV:-${REPO_ROOT}/data/dinos.csv}"

# instalar deps si la primera vez
if ! python3 -c "import fastapi, uvicorn, torch" 2>/dev/null; then
  pip install -q -r requirements.txt
fi

echo "→ levantando generator API en :${PORT} (CHECKPOINT=${CHECKPOINT})"
nohup python3 -m uvicorn Parte_1_Generador_Caracteres.api.main:app \
    --host 0.0.0.0 --port "$PORT" \
    > /home/ec2-user/SageMaker/logs/generator_api.log 2>&1 &

echo "PID: $!"
echo "Logs: /home/ec2-user/SageMaker/logs/generator_api.log"
