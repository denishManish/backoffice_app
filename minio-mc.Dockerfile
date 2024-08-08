FROM minio/mc

COPY minio_setup.sh /usr/local/bin/minio_setup.sh

RUN chmod +x /usr/local/bin/minio_setup.sh
