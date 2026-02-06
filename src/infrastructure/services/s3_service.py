import aioboto3
from uuid import uuid4
from typing import BinaryIO
from botocore.exceptions import ClientError

from domain.interfaces.services.storage import IStorageService
from infrastructure.config import settings


class S3Service(IStorageService):
    def __init__(self):
        self.session = aioboto3.Session()
        self.bucket_name = settings.S3_BUCKET_NAME

        self.aws_config = {
            "aws_access_key_id": settings.AWS_ACCESS_KEY_ID,
            "aws_secret_access_key": settings.AWS_SECRET_ACCESS_KEY,
            "region_name": settings.AWS_REGION,
        }

    async def upload_file(self, file: BinaryIO, filename: str, content_type: str) -> str:
        extension = filename.split(".")[-1]
        s3_key = f"avatars/{uuid4()}.{extension}"

        async with self.session.client("s3", **self.aws_config) as s3:
            try:
                await s3.upload_fileobj(
                    Fileobj=file,
                    Bucket=self.bucket_name,
                    Key=s3_key,
                    ExtraArgs={"ContentType": content_type}
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