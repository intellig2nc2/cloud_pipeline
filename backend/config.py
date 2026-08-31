import os
from pathlib import Path

from dotenv import load_dotenv


BASE_DIR = Path(__file__).resolve().parent
ENV_PATH = BASE_DIR.parent / ".env"

load_dotenv(dotenv_path=ENV_PATH)


# OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")


# AWS S3
S3_BUCKET_NAME = os.getenv(
    "S3_BUCKET_NAME",
    "keroro-s3-resource",
)

S3_IMAGE_PREFIX = os.getenv(
    "S3_IMAGE_PREFIX",
    "images",
).strip("/")

AWS_REGION = os.getenv("AWS_REGION")


if not OPENAI_API_KEY:
    raise RuntimeError(
        f"OPENAI_API_KEY를 찾을 수 없습니다. .env 확인: {ENV_PATH}"
    )

if not S3_BUCKET_NAME:
    raise RuntimeError(
        f"S3_BUCKET_NAME을 찾을 수 없습니다. .env 확인: {ENV_PATH}"
    )