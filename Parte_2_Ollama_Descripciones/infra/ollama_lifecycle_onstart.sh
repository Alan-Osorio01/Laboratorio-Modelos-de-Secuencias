#!/usr/bin/env bash
# Lifecycle script on-start para SageMaker Notebook.
# Mueve el Docker data-root a /SageMaker/docker (volumen EBS persistente)
# para que las imágenes Docker y los modelos Ollama sobrevivan entre reinicios.
#
# Cómo configurar:
#   1. En la consola SageMaker → Lifecycle configurations → Create new
#   2. Pegar este script en la pestaña "Start notebook"
#   3. Asignarlo al notebook instance ANTES de crearlo
#
# IMPORTANTE:
#   - Instancia: m5.xlarge (4 vCPU, 16 GB RAM)
#   - Volumen EBS: mínimo 100 GB (obligatorio)
#   - El script debe completar en < 5 minutos (límite de SageMaker)
#   - Todo corre como root en el lifecycle

set -euo pipefail

SAGEMAKER_DIR="/home/ec2-user/SageMaker"
DOCKER_ROOT="${SAGEMAKER_DIR}/docker"
OLLAMA_DIR="${SAGEMAKER_DIR}/ollama"
MODELS_DIR="${SAGEMAKER_DIR}/models"
LOGS_DIR="${SAGEMAKER_DIR}/logs"

# ---------------------------------------------------------------------------
# 1. Crear directorios persistentes
# ---------------------------------------------------------------------------
echo "[lifecycle] creando directorios en EBS..."
mkdir -p "$DOCKER_ROOT" "$OLLAMA_DIR" "$MODELS_DIR" "$LOGS_DIR"
chown -R ec2-user:ec2-user "$SAGEMAKER_DIR"

# ---------------------------------------------------------------------------
# 2. Mover Docker data-root a EBS (solo si no está ya apuntando ahí)
# ---------------------------------------------------------------------------
CURRENT_ROOT=$(docker info 2>/dev/null | grep "Docker Root Dir" | awk '{print $NF}' || echo "")

if [[ "$CURRENT_ROOT" != "$DOCKER_ROOT" ]]; then
    echo "[lifecycle] moviendo Docker data-root a ${DOCKER_ROOT}..."

    # Detener Docker antes de reconfigurar
    systemctl stop docker || service docker stop || true

    # Escribir daemon.json apuntando al nuevo data-root
    cat > /etc/docker/daemon.json <<EOF
{
    "data-root": "${DOCKER_ROOT}",
    "log-driver": "json-file",
    "log-opts": {
        "max-size": "100m",
        "max-file": "3"
    }
}
EOF

    # Si hay datos en el root original, moverlos (solo primera vez)
    ORIGINAL_ROOT="/var/lib/docker"
    if [[ -d "$ORIGINAL_ROOT" ]] && [[ "$(ls -A $ORIGINAL_ROOT 2>/dev/null)" ]]; then
        echo "[lifecycle] migrando datos existentes de ${ORIGINAL_ROOT} a ${DOCKER_ROOT}..."
        rsync -a --remove-source-files "$ORIGINAL_ROOT/" "$DOCKER_ROOT/" || true
    fi

    # Reiniciar Docker con el nuevo data-root
    systemctl start docker || service docker start
    sleep 5

    NEW_ROOT=$(docker info 2>/dev/null | grep "Docker Root Dir" | awk '{print $NF}' || echo "desconocido")
    echo "[lifecycle] Docker data-root ahora en: ${NEW_ROOT}"
else
    echo "[lifecycle] Docker data-root ya está en ${DOCKER_ROOT}, sin cambios"
fi

# ---------------------------------------------------------------------------
# 3. Verificar espacio en disco
# ---------------------------------------------------------------------------
AVAILABLE_GB=$(df -BG "$SAGEMAKER_DIR" | awk 'NR==2 {gsub(/G/,"",$4); print $4}')
echo "[lifecycle] espacio disponible en EBS: ${AVAILABLE_GB} GB"
if [[ "$AVAILABLE_GB" -lt 20 ]]; then
    echo "[lifecycle] ADVERTENCIA: menos de 20 GB disponibles — considera limpiar con docker system prune -a"
fi

# ---------------------------------------------------------------------------
# 4. Levantar Ollama si el contenedor existe (reinicios posteriores)
# ---------------------------------------------------------------------------
if docker ps -a --format '{{.Names}}' 2>/dev/null | grep -q "^ollama$"; then
    if ! docker ps --format '{{.Names}}' 2>/dev/null | grep -q "^ollama$"; then
        echo "[lifecycle] reiniciando contenedor Ollama..."
        docker start ollama || true
    else
        echo "[lifecycle] Ollama ya está corriendo"
    fi
else
    echo "[lifecycle] contenedor Ollama no existe aún — correr ollama_docker_run.sh manualmente"
fi

# ---------------------------------------------------------------------------
# 5. Levantar FastAPI del generador si ya hay checkpoint
# ---------------------------------------------------------------------------
CHECKPOINT="${MODELS_DIR}/best_model.pt"
REPO_DIR="${SAGEMAKER_DIR}/Laboratorio-Modelos-de-Secuencias"
API_LOG="${LOGS_DIR}/generator_api.log"

if [[ -f "$CHECKPOINT" ]] && [[ -d "$REPO_DIR" ]]; then
    echo "[lifecycle] checkpoint encontrado — reiniciando generator API..."
    # Matar instancia previa si existe
    pkill -f "uvicorn Parte_1_Generador_Caracteres.api.main" || true
    sleep 2
    cd "$REPO_DIR"
    export CHECKPOINT="$CHECKPOINT"
    export DATA_CSV="${REPO_DIR}/data/dinos.csv"
    nohup python3 -m uvicorn Parte_1_Generador_Caracteres.api.main:app \
        --host 0.0.0.0 --port 8000 \
        > "$API_LOG" 2>&1 &
    echo "[lifecycle] generator API iniciado (log: ${API_LOG})"
else
    echo "[lifecycle] sin checkpoint o repo — generator API no iniciado"
    echo "[lifecycle]   checkpoint esperado: ${CHECKPOINT}"
    echo "[lifecycle]   repo esperado:       ${REPO_DIR}"
fi

echo "[lifecycle] on-start completado"
