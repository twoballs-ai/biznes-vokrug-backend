import io
import os
from dotenv import load_dotenv
from minio import Minio, S3Error

# Load environment variables from .env file
load_dotenv()

MINIO_URL = os.getenv("MINIO_URL", "127.0.0.1:9000")
MINIO_ACCESS_KEY = os.getenv("MINIO_ACCESS_KEY", "minioadmin")
MINIO_SECRET_KEY = os.getenv("MINIO_SECRET_KEY", "minioadmin")
BUCKET_NAME = "organizations"

minio_client = Minio(
    endpoint=MINIO_URL,
    access_key=MINIO_ACCESS_KEY,
    secret_key=MINIO_SECRET_KEY,
    secure=False
)

def create_bucket(bucket_name: str = BUCKET_NAME):
    if not minio_client.bucket_exists(bucket_name):
        minio_client.make_bucket(bucket_name)

def upload_image(file_name: str, file_data: bytes, content_type: str) -> str:
    try:
        try:
            minio_client.stat_object(BUCKET_NAME, file_name)
            raise Exception(f"File {file_name} already exists")
        except S3Error as e:
            if e.code != "NoSuchKey":
                raise

        minio_client.put_object(
            BUCKET_NAME,
            file_name,
            data=io.BytesIO(file_data),
            length=len(file_data),
            content_type=content_type
        )
        return f"http://{MINIO_URL}/{BUCKET_NAME}/{file_name}"
    except S3Error as e:
        raise Exception(f"Failed to upload file: {e}")
    except Exception as e:
        raise e

def download_file(file_name: str):
    try:
        response = minio_client.get_object(BUCKET_NAME, file_name)
        return response
    except S3Error as e:
        raise Exception(f"Failed to download file: {e}")

def delete_object(file_name: str):
    try:
        minio_client.remove_object(BUCKET_NAME, file_name)
    except S3Error as err:
        raise Exception(f"Failed to delete object {file_name} from MinIO: {err}")

# Create bucket at initialization
create_bucket()
