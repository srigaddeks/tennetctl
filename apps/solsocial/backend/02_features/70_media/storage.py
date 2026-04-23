"""
Media storage backed by MinIO (S3-compatible).

Bucket: `solsocial-media`, created on first use. Objects are stored under
`{workspace_id}/{uuid}.{ext}`. Files are served through MinIO's public
endpoint (the dev stack exposes :9000 directly; prod would front it with a
signed-URL proxy or a CDN).

Why MinIO: tennetctl already runs it in the dev stack for other purposes.
Zero new infra. For prod, the same boto3 client works against real S3 by
swapping `endpoint_url`.
"""

from __future__ import annotations

import os
from importlib import import_module
from typing import Any

import boto3
from botocore.client import Config
from botocore.exceptions import ClientError

_id = import_module("apps.solsocial.backend.01_core.id")

BUCKET = "solsocial-media"


def _client() -> Any:
    return boto3.client(
        "s3",
        endpoint_url=os.environ.get("SOLSOCIAL_S3_ENDPOINT", "http://localhost:9000"),
        aws_access_key_id=os.environ.get("SOLSOCIAL_S3_KEY", "tennetctl"),
        aws_secret_access_key=os.environ.get("SOLSOCIAL_S3_SECRET", "tennetctl_dev"),
        config=Config(signature_version="s3v4"),
        region_name="us-east-1",
    )


def _ensure_bucket() -> None:
    s3 = _client()
    try:
        s3.head_bucket(Bucket=BUCKET)
    except ClientError as exc:
        code = exc.response.get("Error", {}).get("Code", "")
        if code in ("NoSuchBucket", "404"):
            s3.create_bucket(Bucket=BUCKET)
            # Make objects readable by URL (dev convenience; prod should
            # serve via signed URLs instead of public policy).
            s3.put_bucket_policy(
                Bucket=BUCKET,
                Policy=(
                    '{"Version":"2012-10-17","Statement":[{"Effect":"Allow",'
                    '"Principal":"*","Action":"s3:GetObject",'
                    f'"Resource":"arn:aws:s3:::{BUCKET}/*"'
                    "}]}"
                ),
            )
        else:
            raise


_EXT_MIME = {
    "image/jpeg": "jpg", "image/jpg": "jpg", "image/png": "png",
    "image/gif": "gif", "image/webp": "webp",
    "video/mp4": "mp4", "video/quicktime": "mov",
}


def _ext_for(content_type: str, filename: str) -> str:
    if content_type in _EXT_MIME:
        return _EXT_MIME[content_type]
    if "." in filename:
        return filename.rsplit(".", 1)[-1].lower()
    return "bin"


def upload(
    *, workspace_id: str, data: bytes, content_type: str, filename: str,
) -> dict:
    """Upload a file to `{workspace_id}/{uuid}.{ext}`. Returns {url, key, size, content_type}."""
    _ensure_bucket()
    ext = _ext_for(content_type, filename)
    key = f"{workspace_id}/{_id.uuid7()}.{ext}"
    s3 = _client()
    s3.put_object(
        Bucket=BUCKET, Key=key, Body=data, ContentType=content_type,
        ACL="public-read",
    )
    public_base = os.environ.get(
        "SOLSOCIAL_S3_PUBLIC_BASE",
        os.environ.get("SOLSOCIAL_S3_ENDPOINT", "http://localhost:9000"),
    ).rstrip("/")
    url = f"{public_base}/{BUCKET}/{key}"
    return {
        "url": url, "key": key, "size": len(data),
        "content_type": content_type,
    }
