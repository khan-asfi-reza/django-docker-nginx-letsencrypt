from copy import deepcopy

from boto3 import session
from botocore.client import BaseClient
from django.conf import settings
from django.core.files import File


class S3BucketError(Exception):
    pass


class S3Storage:
    __bucket_keys = [
        "bucket",
        "endpoint_url",
        "access_key_id",
        "access_key",
        "region",
        "acl",
        "default_location",
    ]

    def set_bucket(self):
        """
        Set bucket registry
        """
        buckets = deepcopy(settings.DIGITAL_OCEAN_BUCKETS)
        if "default" not in buckets:
            raise S3BucketError("'default' bucket missing error")

        for bucket, values in buckets.items():
            for key in self.__bucket_keys:
                if key not in values:
                    raise S3BucketError(f"'{key}' missing in bucket details")
        return buckets

    def create_session(self):
        """
        Create session
        """
        if not self.session:
            return session.Session()

    def create_client(self):
        """
        Create sessions for each bucket
        """
        _clients = {}
        for bucket, bucket_details in self.buckets.items():
            _clients[bucket] = self.session.client(
                service_name="s3",
                region_name="nyc3",
                aws_access_key_id=bucket_details["access_key_id"],
                aws_secret_access_key=bucket_details["access_key"],
                endpoint_url=bucket_details["endpoint_url"]
            )
        return _clients

    def __init__(self):
        """
        Settings folder must have digital ocean bucket list
        """
        self.session = session.Session()
        self.buckets = self.set_bucket()
        self.clients: dict[str, BaseClient] = self.create_client()

    def get_client_with_bucket(self, bucket) -> tuple[BaseClient, dict[str, str]]:
        """
        Get bucket client along with bucket details
        """
        if bucket not in self.buckets:
            raise S3BucketError(f"Invalid bucket '{bucket}'")

        client = self.clients[bucket]
        bucket_details = self.buckets[bucket]
        return client, bucket_details

    def upload_file(self,
                    file: bytes | File,
                    file_name: str,
                    upload_path: str = "",
                    bucket: str = "default",
                    content_type=""
                    ):
        """
        Upload file to space ( Not space, digital ocean space ) bucket
        Args:
            bucket: str
            file: bytes | File
            upload_path: str
            file_name: str
            content_type: str

        Returns: URL of the file
        """
        if bucket not in self.buckets:
            raise S3BucketError(f"Invalid bucket '{bucket}'")

        client = self.clients[bucket]
        bucket_details = self.buckets[bucket]
        if not upload_path:
            upload_path = bucket_details["default_location"]
        kwargs = {}
        if content_type:
            kwargs["ContentType"] = content_type
        full_path = f"{upload_path}/{file_name}"
        response = client.put_object(
            Body=file,
            Bucket=bucket_details["bucket"],
            Key=full_path,
            ACL=bucket_details["acl"],
            **kwargs
        )
        if not response["ResponseMetadata"]["HTTPStatusCode"] == 200:
            raise S3BucketError(
                "File upload failed"
            )
        return f"{bucket_details['endpoint_url']}/{bucket_details['bucket']}/{full_path}"


StorageService = S3Storage()
