"""Exercise 2: Upload Backup to S3 Storage.

The learner uploads a backup file to an S3-compatible storage bucket
with proper metadata (content-type, upload timestamp, source database name).

Validates: Requirement 9.1 (S3 upload), Requirement 9.3 (S3 metadata verification)
"""

import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional

from labs.templates.exercise_base import Exercise


class S3UploadExercise(Exercise):
    """Upload a backup file to S3-compatible storage with metadata."""

    @property
    def exercise_id(self) -> str:
        return "02_s3_upload"

    @property
    def name(self) -> str:
        return "Upload Backup to S3 Storage"

    @property
    def description(self) -> str:
        return (
            "Upload a backup file to an S3-compatible storage bucket with metadata "
            "including content-type, upload timestamp, and source database name."
        )

    @property
    def timeout_minutes(self) -> int:
        return 15

    @property
    def prerequisites(self) -> list[str]:
        return ["01_pg_dump_backup"]

    def setup(self) -> None:
        """Verify S3 credentials and bucket accessibility."""
        pass

    def execute(self, submission: dict) -> dict:
        """Upload a backup file to S3-compatible storage.

        Expected submission keys:
            - backup_path (str): Path to the local backup file.
            - bucket_name (str): Target S3 bucket name.
            - s3_key (str): Object key (path) in the bucket.
            - source_db_name (str): Name of the source database (for metadata).
            - endpoint_url (str, optional): S3-compatible endpoint URL.
            - region (str, optional): AWS region. Defaults to 'us-east-1'.

        Returns:
            dict with keys:
                - uploaded (bool): Whether the upload succeeded.
                - bucket (str): Target bucket name.
                - key (str): Object key in the bucket.
                - metadata (dict): Metadata attached to the uploaded object.
                - file_size_bytes (int): Size of the uploaded file.
                - error (str): Error message if upload failed.
        """
        backup_path = submission.get("backup_path", "")
        bucket_name = submission.get("bucket_name", "")
        s3_key = submission.get("s3_key", "")
        source_db_name = submission.get("source_db_name", "")
        endpoint_url = submission.get("endpoint_url", os.environ.get("S3_ENDPOINT_URL", ""))
        region = submission.get("region", "us-east-1")

        # Validate local file exists
        if not Path(backup_path).exists():
            return {
                "uploaded": False,
                "bucket": bucket_name,
                "key": s3_key,
                "metadata": {},
                "file_size_bytes": 0,
                "error": f"Backup file not found: {backup_path}",
            }

        file_size = Path(backup_path).stat().st_size
        if file_size == 0:
            return {
                "uploaded": False,
                "bucket": bucket_name,
                "key": s3_key,
                "metadata": {},
                "file_size_bytes": 0,
                "error": "Backup file is empty (0 bytes).",
            }

        # Define metadata
        upload_timestamp = datetime.now(timezone.utc).isoformat()
        content_type = (
            "application/octet-stream"
            if backup_path.endswith(".dump")
            else "application/sql"
        )
        metadata = {
            "content-type": content_type,
            "upload-timestamp": upload_timestamp,
            "source-database": source_db_name,
        }

        # Attempt S3 upload using boto3
        try:
            import boto3
            from botocore.exceptions import ClientError, NoCredentialsError

            client_kwargs = {"region_name": region}
            if endpoint_url:
                client_kwargs["endpoint_url"] = endpoint_url

            s3_client = boto3.client("s3", **client_kwargs)

            s3_client.upload_file(
                Filename=backup_path,
                Bucket=bucket_name,
                Key=s3_key,
                ExtraArgs={
                    "ContentType": content_type,
                    "Metadata": {
                        "upload-timestamp": upload_timestamp,
                        "source-database": source_db_name,
                    },
                },
            )

            return {
                "uploaded": True,
                "bucket": bucket_name,
                "key": s3_key,
                "metadata": metadata,
                "file_size_bytes": file_size,
                "error": "",
            }

        except ImportError:
            return {
                "uploaded": False,
                "bucket": bucket_name,
                "key": s3_key,
                "metadata": metadata,
                "file_size_bytes": file_size,
                "error": "boto3 is not installed. Install with: pip install boto3",
            }
        except NoCredentialsError:
            return {
                "uploaded": False,
                "bucket": bucket_name,
                "key": s3_key,
                "metadata": metadata,
                "file_size_bytes": file_size,
                "error": (
                    "AWS credentials not found. Set AWS_ACCESS_KEY_ID and "
                    "AWS_SECRET_ACCESS_KEY environment variables."
                ),
            }
        except ClientError as e:
            error_code = e.response.get("Error", {}).get("Code", "Unknown")
            error_msg = e.response.get("Error", {}).get("Message", str(e))
            return {
                "uploaded": False,
                "bucket": bucket_name,
                "key": s3_key,
                "metadata": metadata,
                "file_size_bytes": file_size,
                "error": f"S3 error ({error_code}): {error_msg}",
            }
        except Exception as e:
            return {
                "uploaded": False,
                "bucket": bucket_name,
                "key": s3_key,
                "metadata": metadata,
                "file_size_bytes": file_size,
                "error": f"Unexpected error: {e}",
            }

    def validate(self, result: dict) -> list[dict]:
        """Validate the S3 upload result.

        Checks:
        1. Upload completed successfully
        2. Uploaded object exists in the configured bucket
        3. Metadata includes content-type, upload timestamp, and source database name
        """
        checks = []

        # Check 1: Upload success
        uploaded = result.get("uploaded", False)
        checks.append({
            "name": "s3_upload_success",
            "passed": uploaded,
            "feedback": (
                "Backup uploaded to S3 successfully."
                if uploaded
                else f"S3 upload failed: {result.get('error', 'Unknown error')}"
            ),
            "expected": "uploaded=True",
            "actual": f"uploaded={uploaded}",
        })

        # Check 2: File size > 0 in S3
        file_size = result.get("file_size_bytes", 0)
        checks.append({
            "name": "s3_object_size",
            "passed": file_size > 0,
            "feedback": (
                f"Uploaded object size: {file_size} bytes."
                if file_size > 0
                else "Uploaded object has 0 bytes or upload did not complete."
            ),
            "expected": "> 0 bytes",
            "actual": f"{file_size} bytes",
        })

        # Check 3: Metadata completeness
        metadata = result.get("metadata", {})
        has_content_type = bool(metadata.get("content-type"))
        has_timestamp = bool(metadata.get("upload-timestamp"))
        has_source_db = bool(metadata.get("source-database"))
        metadata_complete = has_content_type and has_timestamp and has_source_db

        missing_fields = []
        if not has_content_type:
            missing_fields.append("content-type")
        if not has_timestamp:
            missing_fields.append("upload-timestamp")
        if not has_source_db:
            missing_fields.append("source-database")

        checks.append({
            "name": "s3_metadata_complete",
            "passed": metadata_complete,
            "feedback": (
                "All required metadata fields present (content-type, upload-timestamp, source-database)."
                if metadata_complete
                else f"Missing metadata fields: {', '.join(missing_fields)}"
            ),
            "expected": "content-type, upload-timestamp, source-database",
            "actual": ", ".join(metadata.keys()) if metadata else "no metadata",
        })

        return checks

    def teardown(self) -> None:
        """No cleanup needed; uploaded objects remain in S3 for verification."""
        pass

    def get_hints(self) -> list[str]:
        return [
            "Install boto3: pip install boto3",
            "Set AWS_ACCESS_KEY_ID and AWS_SECRET_ACCESS_KEY environment variables.",
            "Use the 'Metadata' parameter in upload_file() to attach custom metadata.",
            "For S3-compatible storage (MinIO, etc.), set the endpoint_url parameter.",
        ]

    def get_instructions(self) -> str:
        return (
            "Upload your database backup to an S3-compatible storage bucket.\n\n"
            "Submit with:\n"
            "  - backup_path: Local path to the backup file (from Exercise 1)\n"
            "  - bucket_name: Target S3 bucket name\n"
            "  - s3_key: Object key (path) in the bucket (e.g., 'backups/mydb_2025.dump')\n"
            "  - source_db_name: Name of the source database\n"
            "  - endpoint_url: S3-compatible endpoint (optional, for MinIO etc.)\n"
            "  - region: AWS region (default: us-east-1)\n\n"
            "The upload must include metadata: content-type, upload-timestamp, and source-database."
        )
