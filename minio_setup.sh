#!/bin/sh

set -a
. /app/.env
set +a

mc alias set myminio $MINIO_SERVER_URL $MINIO_ROOT_USER $MINIO_ROOT_PASSWORD
mc mb myminio/$MINIO_BUCKET_NAME --ignore-existing
echo 'Bucket setup completed.'

exec "$@"
