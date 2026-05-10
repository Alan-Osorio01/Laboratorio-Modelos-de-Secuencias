"""
Provisiona toda la infraestructura de hosting del frontend en AWS Academy.

Crea (o reutiliza si ya existen):
  - Bucket S3 con static website hosting y política pública
  - Distribución CloudFront apuntando al bucket
  - Sube los archivos de web/ al bucket

Al final imprime las URLs listas para usar.

Uso:
    python Parte_4_Integracion_Web/infra/provision_aws.py

Variables de entorno opcionales:
    AWS_REGION              — default: us-east-1
    S3_BUCKET_SUFFIX        — sufijo para el nombre del bucket (default: dino-lab)
    SKIP_CLOUDFRONT         — si es '1', salta la creación de CloudFront (más rápido para pruebas)
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

import boto3
from botocore.exceptions import ClientError

# ---------------------------------------------------------------------------
# Cargar .env.aws desde la raíz del repo (credenciales de Academy)
# ---------------------------------------------------------------------------
_REPO_ROOT = Path(__file__).parent.parent.parent
_ENV_AWS = _REPO_ROOT / ".env.aws"

if _ENV_AWS.exists():
    for _line in _ENV_AWS.read_text().splitlines():
        _line = _line.strip()
        if _line and not _line.startswith("#") and "=" in _line:
            _key, _, _val = _line.partition("=")
            if _val and _key not in os.environ:
                os.environ[_key.strip()] = _val.strip()
    print(f"[credentials] cargadas desde {_ENV_AWS}")
else:
    print(f"[credentials] {_ENV_AWS} no encontrado — usando credenciales del entorno o ~/.aws/credentials")

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
REGION = os.environ.get("AWS_REGION", "us-east-1")
SUFFIX = os.environ.get("S3_BUCKET_SUFFIX", "dino-lab")
BUCKET_NAME = f"frontend-{SUFFIX}"
SKIP_CF = os.environ.get("SKIP_CLOUDFRONT", "0") == "1"

WEB_DIR = Path(__file__).parent.parent / "web"

CONTENT_TYPES: dict[str, str] = {
    ".html": "text/html; charset=utf-8",
    ".css":  "text/css",
    ".js":   "application/javascript",
    ".json": "application/json",
    ".png":  "image/png",
    ".jpg":  "image/jpeg",
    ".svg":  "image/svg+xml",
    ".ico":  "image/x-icon",
}

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(msg: str) -> None:
    print(f"  {msg}", flush=True)


def _create_or_reuse_bucket(s3, s3_client) -> str:
    """Crea el bucket o lo reutiliza si ya existe. Devuelve el website endpoint."""
    try:
        if REGION == "us-east-1":
            s3_client.create_bucket(Bucket=BUCKET_NAME)
        else:
            s3_client.create_bucket(
                Bucket=BUCKET_NAME,
                CreateBucketConfiguration={"LocationConstraint": REGION},
            )
        _log(f"bucket creado: {BUCKET_NAME}")
    except ClientError as e:
        code = e.response["Error"]["Code"]
        if code in ("BucketAlreadyOwnedByYou", "BucketAlreadyExists"):
            _log(f"bucket ya existe, reutilizando: {BUCKET_NAME}")
        else:
            raise

    # Deshabilitar Block Public Access
    s3_client.put_public_access_block(
        Bucket=BUCKET_NAME,
        PublicAccessBlockConfiguration={
            "BlockPublicAcls": False,
            "IgnorePublicAcls": False,
            "BlockPublicPolicy": False,
            "RestrictPublicBuckets": False,
        },
    )
    _log("Block Public Access deshabilitado")

    # Política pública de lectura
    policy = json.dumps({
        "Version": "2012-10-17",
        "Statement": [{
            "Sid": "PublicRead",
            "Effect": "Allow",
            "Principal": "*",
            "Action": "s3:GetObject",
            "Resource": f"arn:aws:s3:::{BUCKET_NAME}/*",
        }],
    })
    s3_client.put_bucket_policy(Bucket=BUCKET_NAME, Policy=policy)
    _log("política pública aplicada")

    # Static website hosting
    s3_client.put_bucket_website(
        Bucket=BUCKET_NAME,
        WebsiteConfiguration={
            "IndexDocument": {"Suffix": "index.html"},
            "ErrorDocument": {"Key": "index.html"},
        },
    )
    _log("static website hosting habilitado")

    return f"http://{BUCKET_NAME}.s3-website-{REGION}.amazonaws.com"


def _upload_web_files(s3_client) -> None:
    """Sube todos los archivos de web/ al bucket (excepto los .sh)."""
    files = [
        f for f in WEB_DIR.rglob("*")
        if f.is_file() and f.suffix != ".sh"
    ]
    for f in files:
        key = f.relative_to(WEB_DIR).as_posix()
        content_type = CONTENT_TYPES.get(f.suffix, "application/octet-stream")
        s3_client.upload_file(
            str(f),
            BUCKET_NAME,
            key,
            ExtraArgs={
                "ContentType": content_type,
                "CacheControl": "public, max-age=300",
            },
        )
        _log(f"subido: {key}")


def _create_or_reuse_cloudfront(cf_client, s3_website_endpoint: str) -> tuple[str, str]:
    """
    Crea una distribución CloudFront o devuelve la primera existente
    que ya apunte al mismo bucket.
    Devuelve (distribution_id, domain_name).
    """
    # Buscar si ya existe una distribución para este bucket
    paginator = cf_client.get_paginator("list_distributions")
    for page in paginator.paginate():
        items = page.get("DistributionList", {}).get("Items", [])
        for dist in items:
            origins = dist.get("Origins", {}).get("Items", [])
            for origin in origins:
                if BUCKET_NAME in origin.get("DomainName", ""):
                    dist_id = dist["Id"]
                    domain  = dist["DomainName"]
                    _log(f"distribución existente reutilizada: {dist_id}")
                    return dist_id, domain

    # Crear nueva distribución
    origin_domain = f"{BUCKET_NAME}.s3-website-{REGION}.amazonaws.com"
    response = cf_client.create_distribution(
        DistributionConfig={
            "CallerReference": f"dino-lab-{int(time.time())}",
            "Comment": "Dino Lab frontend",
            "Enabled": True,
            "PriceClass": "PriceClass_100",
            "DefaultRootObject": "index.html",
            "Origins": {
                "Quantity": 1,
                "Items": [{
                    "Id": "S3WebsiteOrigin",
                    "DomainName": origin_domain,
                    "CustomOriginConfig": {
                        "HTTPPort": 80,
                        "HTTPSPort": 443,
                        "OriginProtocolPolicy": "http-only",
                    },
                }],
            },
            "DefaultCacheBehavior": {
                "TargetOriginId": "S3WebsiteOrigin",
                "ViewerProtocolPolicy": "redirect-to-https",
                "CachePolicyId": "658327ea-f89d-4fab-a63d-7e88639e58f6",  # CachingOptimized
                "AllowedMethods": {
                    "Quantity": 2,
                    "Items": ["GET", "HEAD"],
                    "CachedMethods": {"Quantity": 2, "Items": ["GET", "HEAD"]},
                },
                "Compress": True,
            },
            "CustomErrorResponses": {
                "Quantity": 1,
                "Items": [{
                    "ErrorCode": 403,
                    "ResponseCode": "200",
                    "ResponsePagePath": "/index.html",
                    "ErrorCachingMinTTL": 10,
                }],
            },
            "ViewerCertificate": {
                "CloudFrontDefaultCertificate": True,
                "MinimumProtocolVersion": "TLSv1.2_2021",
            },
        }
    )
    dist   = response["Distribution"]
    dist_id = dist["Id"]
    domain  = dist["DomainName"]
    _log(f"distribución CloudFront creada: {dist_id}")
    _log("(puede tardar ~10–15 min en estar activa globalmente)")
    return dist_id, domain


def _invalidate_cache(cf_client, dist_id: str) -> None:
    cf_client.create_invalidation(
        DistributionId=dist_id,
        InvalidationBatch={
            "Paths": {"Quantity": 1, "Items": ["/*"]},
            "CallerReference": str(int(time.time())),
        },
    )
    _log("invalidación de caché enviada")


def _write_config_js(cf_domain: str) -> None:
    """Actualiza config.js con el dominio de CloudFront como referencia."""
    config_path = WEB_DIR / "config.js"
    current = config_path.read_text()
    # Solo escribe si los placeholders no han sido reemplazados aún
    if "REPLACE_ME" not in current:
        _log("config.js ya tiene URLs reales, no se sobreescribe")
        return
    _log("config.js sigue con placeholders — recuerda actualizarlo con las URLs de ngrok antes del deploy final")


def _save_outputs(s3_url: str, cf_id: str, cf_domain: str) -> None:
    """Actualiza .env.aws en la raíz del repo con los IDs de los recursos creados."""
    env_path = _REPO_ROOT / ".env.aws"

    # Leer líneas existentes (credenciales + lo que ya había)
    existing: dict[str, str] = {}
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            line = line.strip()
            if line and not line.startswith("#") and "=" in line:
                k, _, v = line.partition("=")
                existing[k.strip()] = v.strip()

    # Actualizar solo los IDs de infraestructura
    existing["S3_BUCKET"] = BUCKET_NAME
    existing["CLOUDFRONT_DISTRIBUTION"] = cf_id
    existing["CLOUDFRONT_DOMAIN"] = f"https://{cf_domain}"
    existing["S3_WEBSITE"] = s3_url

    # Reescribir preservando credenciales
    lines = ["# Generado por provision_aws.py — no commitear\n"]
    for k, v in existing.items():
        lines.append(f"{k}={v}\n")
    env_path.write_text("".join(lines))
    _log(f"IDs de infraestructura guardados en {env_path}")


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    session   = boto3.Session(region_name=REGION)
    s3_client = session.client("s3")
    cf_client = session.client("cloudfront")

    print(f"\n[1/4] Configurando bucket S3: {BUCKET_NAME}")
    s3_website = _create_or_reuse_bucket(None, s3_client)

    print(f"\n[2/4] Subiendo archivos de {WEB_DIR.name}/")
    _upload_web_files(s3_client)

    if SKIP_CF:
        print("\n[3/4] SKIP_CLOUDFRONT=1 — saltando CloudFront")
        print("\n✓ Deploy completo (solo S3)")
        print(f"  URL S3:  {s3_website}")
        return

    print("\n[3/4] Configurando CloudFront")
    cf_id, cf_domain = _create_or_reuse_cloudfront(cf_client, s3_website)

    print("\n[4/4] Invalidando caché")
    _invalidate_cache(cf_client, cf_id)

    _write_config_js(cf_domain)
    _save_outputs(s3_website, cf_id, cf_domain)

    print("\n" + "=" * 60)
    print("✓  Infraestructura lista")
    print(f"   S3 bucket:         {BUCKET_NAME}")
    print(f"   S3 website URL:    {s3_website}")
    print(f"   CloudFront ID:     {cf_id}")
    print(f"   CloudFront URL:    https://{cf_domain}  ← esta es la URL pública")
    print("=" * 60)
    print()
    print("Próximo paso: actualiza web/config.js con las URLs de ngrok")
    print("y vuelve a correr este script (los archivos se resuben automáticamente).")
    print()


if __name__ == "__main__":
    try:
        main()
    except ClientError as e:
        print(f"\n[ERROR] AWS: {e.response['Error']['Message']}", file=sys.stderr)
        print("Verifica que tus credenciales de Academy estén activas (aws configure).", file=sys.stderr)
        sys.exit(1)
