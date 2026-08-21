import asyncio
from dataclasses import dataclass
from typing import Protocol

from botocore.exceptions import ClientError
from fastapi import Request

from app.core.config import settings


@dataclass(frozen=True)
class StoredExport:
    content: bytes
    filename: str


class ExportStorage(Protocol):
    async def ready(self) -> None: ...
    async def put(self, file_id: str, content: bytes, filename: str) -> None: ...
    async def get(self, file_id: str) -> StoredExport | None: ...
    async def close(self) -> None: ...


class LocalExportStorage:
    async def ready(self) -> None:
        from app.services import csv_cleaner

        await asyncio.to_thread(csv_cleaner.OUTPUT_DIR.mkdir, parents=True, exist_ok=True)

    async def put(self, file_id: str, content: bytes, filename: str) -> None:
        from app.services import csv_cleaner

        await asyncio.to_thread(csv_cleaner.persist_local_export, file_id, content, filename)

    async def get(self, file_id: str) -> StoredExport | None:
        from app.services import csv_cleaner

        result = await asyncio.to_thread(csv_cleaner.read_local_export, file_id)
        if result is None:
            return None
        content, filename = result
        return StoredExport(content=content, filename=filename)

    async def close(self) -> None:
        return None


class S3ExportStorage:
    def __init__(
        self,
        *,
        bucket: str,
        prefix: str,
        region: str,
        endpoint_url: str | None = None,
        access_key_id: str | None = None,
        secret_access_key: str | None = None,
        client=None,
    ) -> None:
        self.bucket = bucket
        self.prefix = prefix.strip("/")
        self.region = region
        if client is not None:
            self._client = client
            return

        import boto3

        kwargs = {
            "region_name": region,
            "endpoint_url": endpoint_url,
        }
        if access_key_id and secret_access_key:
            kwargs["aws_access_key_id"] = access_key_id
            kwargs["aws_secret_access_key"] = secret_access_key
        self._client = boto3.client("s3", **kwargs)

    def _key(self, file_id: str) -> str:
        name = f"{file_id}.csv"
        return f"{self.prefix}/{name}" if self.prefix else name

    async def ready(self) -> None:
        await asyncio.to_thread(self._client.head_bucket, Bucket=self.bucket)

    async def put(self, file_id: str, content: bytes, filename: str) -> None:
        await asyncio.to_thread(
            self._client.put_object,
            Bucket=self.bucket,
            Key=self._key(file_id),
            Body=content,
            ContentType="text/csv",
            ServerSideEncryption="AES256",
            Metadata={"filename": filename},
        )

    async def get(self, file_id: str) -> StoredExport | None:
        try:
            response = await asyncio.to_thread(
                self._client.get_object,
                Bucket=self.bucket,
                Key=self._key(file_id),
            )
        except ClientError as exc:
            code = str(exc.response.get("Error", {}).get("Code", ""))
            if code in {"NoSuchKey", "NoSuchObject", "404", "NotFound"}:
                return None
            raise

        body = response["Body"]
        content = await asyncio.to_thread(body.read)
        filename = response.get("Metadata", {}).get("filename") or f"{file_id}.csv"
        return StoredExport(content=content, filename=filename)

    async def close(self) -> None:
        close = getattr(self._client, "close", None)
        if close is not None:
            await asyncio.to_thread(close)


def build_export_storage() -> ExportStorage:
    if settings.export_storage_backend == "s3":
        return S3ExportStorage(
            bucket=settings.s3_bucket,
            prefix=settings.s3_prefix,
            region=settings.s3_region,
            endpoint_url=settings.s3_endpoint_url,
            access_key_id=settings.s3_access_key_id,
            secret_access_key=settings.s3_secret_access_key,
        )
    return LocalExportStorage()


def get_export_storage(request: Request) -> ExportStorage:
    return request.app.state.export_storage
