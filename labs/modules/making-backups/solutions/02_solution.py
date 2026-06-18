"""Reference solution for Exercise 2: Upload Backup to S3 Storage.

This solution demonstrates uploading a backup file to S3-compatible
storage with proper metadata.
"""


def get_solution_submission() -> dict:
    """Return the reference submission for this exercise.

    Returns:
        A dict with the correct submission parameters.
    """
    return {
        "backup_path": "/tmp/backups/ai_store_db.dump",
        "bucket_name": "ai-store-backups",
        "s3_key": "backups/ai_store_db_2025-01-15.dump",
        "source_db_name": "ai_store_db",
        "endpoint_url": "https://s3.example.com",
        "region": "us-east-1",
    }


def get_explanation() -> str:
    """Return a detailed explanation of the solution approach."""
    return """
Solution: Upload Backup to S3 Storage
=======================================

1. Install boto3 if not already present:
   $ pip install boto3

2. Set AWS/S3 credentials:
   export AWS_ACCESS_KEY_ID='your_access_key'
   export AWS_SECRET_ACCESS_KEY='your_secret_key'
   export S3_ENDPOINT_URL='https://s3.example.com'  # For S3-compatible storage

3. Upload with metadata using boto3:

   import boto3
   from datetime import datetime, timezone

   s3 = boto3.client('s3', endpoint_url='https://s3.example.com')

   s3.upload_file(
       Filename='/tmp/backups/ai_store_db.dump',
       Bucket='ai-store-backups',
       Key='backups/ai_store_db_2025-01-15.dump',
       ExtraArgs={
           'ContentType': 'application/octet-stream',
           'Metadata': {
               'upload-timestamp': datetime.now(timezone.utc).isoformat(),
               'source-database': 'ai_store_db',
           }
       }
   )

Key points:
- Always include metadata for traceability:
  - content-type: identifies the file type
  - upload-timestamp: when the backup was uploaded
  - source-database: which database the backup came from
- Use a structured key naming convention (e.g., backups/{db}_{date}.dump)
- For OVHcloud Object Storage or MinIO, set endpoint_url
- Verify the upload by checking the object exists with head_object()
"""
