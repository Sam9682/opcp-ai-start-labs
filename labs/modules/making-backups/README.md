# Making Backups

## Objective

Learn how to protect application data on the AI-Powered-Store platform by performing PostgreSQL database backups using `pg_dump`, uploading backups to S3-compatible storage, scheduling automated backups with cron, and verifying backup integrity through restoration tests.

## Prerequisites

- Installation on Bare-Metal Ubuntu (install-bare-metal)

## Exercises

| # | Exercise | Objective |
|---|----------|-----------|
| 1 | PostgreSQL Backup with pg_dump | Create a database backup using pg_dump in custom or plain SQL format |
| 2 | Upload Backup to S3 Storage | Upload the backup file to an S3-compatible bucket with proper metadata |
| 3 | Schedule Automated Backups | Configure a cron job to automate periodic database backups |
| 4 | Verify Backup Integrity | Restore a backup to a test database to confirm integrity and completeness |
