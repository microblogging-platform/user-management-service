import aioboto3
from uuid import uuid4
from typing import BinaryIO, Any, Coroutine
from botocore.exceptions import ClientError

from domain.interfaces.services.storage import IStorageService
from infrastructure.config import settings


class S3Service(IStorageService):
    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket_name = settings.s3_bucket_name

        self.aws_config = {
            "aws_access_key_id": settings.aws_access_key_id,
            "aws_secret_access_key": settings.aws_secret_access_key,
            "region_name": settings.aws_region,
        }

    async def upload_file(self, file: BinaryIO, filename: str, content_type: str) -> str:
        extension = filename.split(".")[-1]
        s3_key = f"avatars/{uuid4()}.{extension}"

        async with self.session.client("s3", **self.aws_config) as s3:
            try:
                await s3.upload_fileobj(
                    Fileobj=file, Bucket=self.bucket_name, Key=s3_key, ExtraArgs={"ContentType": content_type}
                )
                return s3_key
            except ClientError as e:
                print(f"S3 Upload Error: {e}")
                raise e

    async def delete_file(self, file_path: str):
        if not file_path:
            return

        async with self.session.client("s3", **self.aws_config) as s3:
            try:
                await s3.delete_object(Bucket=self.bucket_name, Key=file_path)
            except ClientError as e:
                print(f"S3 Delete Error: {e}")

    async def generate_presigned_upload_url(self, object_key: str, content_type: str, expires_in: int = 3600) -> str:
        async with self.session.client("s3", **self.aws_config) as s3:
            try:
                url = await s3.generate_presigned_url(
                    ClientMethod="put_object",
                    Params={"Bucket": self.bucket_name, "Key": object_key, "ContentType": content_type},
                    ExpiresIn=expires_in,
                )
                return url
            except ClientError as e:
                print(f"S3 Presigned URL Error: {e}")
                raise e

    async def generate_presigned_get_url(self, object_key: str, expires_in: int = 3600) -> str | None:
        if not object_key:
            return None

        async with self.session.client("s3", **self.aws_config) as s3:
            try:
                url = await s3.generate_presigned_url(
                    ClientMethod="get_object",
                    Params={"Bucket": self.bucket_name, "Key": object_key},
                    ExpiresIn=expires_in,
                )
                return url
            except Exception as e:
                print(f"Error generating presigned URL: {e}")
                return None
