from io import BytesIO
from pathlib import Path
from typing import BinaryIO
from uuid import uuid4

import boto3
from botocore.exceptions import ClientError

from config import (
    AWS_REGION,
    S3_BUCKET_NAME,
    S3_IMAGE_PREFIX,
)


# EC2 IAM Role 사용
# AWS_REGION이 없으면 boto3 기본 설정을 사용
if AWS_REGION:
    s3_client = boto3.client(
        "s3",
        region_name=AWS_REGION,
    )
else:
    s3_client = boto3.client("s3")


def _build_key(filename: str) -> str:
    """
    filename -> images/filename
    """
    safe_filename = Path(filename).name

    return f"{S3_IMAGE_PREFIX}/{safe_filename}"


def _generate_filename(original_filename: str) -> str:
    """
    파일명 충돌 방지를 위해 UUID 사용
    """
    suffix = Path(original_filename).suffix.lower()

    if not suffix:
        suffix = ".jpg"

    return f"{uuid4()}{suffix}"


# =========================================================
# CREATE
# =========================================================

def upload_image(
    file: bytes | BinaryIO,
    original_filename: str,
    content_type: str | None = None,
) -> dict:
    """
    S3 images/ 폴더에 새 이미지 업로드
    """

    filename = _generate_filename(original_filename)
    key = _build_key(filename)

    extra_args = {}

    if content_type:
        extra_args["ContentType"] = content_type

    try:
        if isinstance(file, bytes):
            file = BytesIO(file)

        s3_client.upload_fileobj(
            file,
            S3_BUCKET_NAME,
            key,
            ExtraArgs=extra_args if extra_args else None,
        )

        return {
            "filename": filename,
            "key": key,
            "bucket": S3_BUCKET_NAME,
        }

    except ClientError as error:
        raise RuntimeError(
            f"S3 이미지 업로드 실패: {error}"
        ) from error


# =========================================================
# READ - 단일 이미지
# =========================================================

def get_image(filename: str) -> dict:
    """
    S3에서 이미지 원본 읽기
    """

    key = _build_key(filename)

    try:
        response = s3_client.get_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
        )

        return {
            "filename": filename,
            "key": key,
            "body": response["Body"].read(),
            "content_type": response.get(
                "ContentType",
                "application/octet-stream",
            ),
            "content_length": response.get(
                "ContentLength",
            ),
        }

    except s3_client.exceptions.NoSuchKey:
        raise FileNotFoundError(
            f"S3 이미지가 존재하지 않습니다: {filename}"
        )

    except ClientError as error:
        if error.response["Error"]["Code"] in (
            "NoSuchKey",
            "404",
        ):
            raise FileNotFoundError(
                f"S3 이미지가 존재하지 않습니다: {filename}"
            )

        raise RuntimeError(
            f"S3 이미지 조회 실패: {error}"
        ) from error


# =========================================================
# READ - 이미지 목록
# =========================================================

def list_images() -> list[dict]:
    """
    s3://bucket/images/ 내부 이미지 전체 목록 조회
    """

    prefix = f"{S3_IMAGE_PREFIX}/"

    images = []
    continuation_token = None

    try:
        while True:
            params = {
                "Bucket": S3_BUCKET_NAME,
                "Prefix": prefix,
            }

            if continuation_token:
                params["ContinuationToken"] = continuation_token

            response = s3_client.list_objects_v2(**params)

            for item in response.get("Contents", []):
                key = item["Key"]

                # images/ 자체는 제외
                if key == prefix:
                    continue

                filename = key.removeprefix(prefix)

                images.append(
                    {
                        "filename": filename,
                        "key": key,
                        "size": item["Size"],
                        "last_modified": (
                            item["LastModified"].isoformat()
                        ),
                    }
                )

            if not response.get("IsTruncated"):
                break

            continuation_token = response.get(
                "NextContinuationToken"
            )

        return images

    except ClientError as error:
        raise RuntimeError(
            f"S3 이미지 목록 조회 실패: {error}"
        ) from error


# =========================================================
# UPDATE
# =========================================================

def update_image(
    filename: str,
    file: bytes | BinaryIO,
    content_type: str | None = None,
) -> dict:
    """
    기존 filename의 객체를 새로운 이미지로 덮어쓰기

    S3는 별도의 UPDATE 명령이 없으므로
    같은 Key에 Put하면 기존 파일이 교체된다.
    """

    key = _build_key(filename)

    extra_args = {}

    if content_type:
        extra_args["ContentType"] = content_type

    try:
        if isinstance(file, bytes):
            file = BytesIO(file)

        s3_client.upload_fileobj(
            file,
            S3_BUCKET_NAME,
            key,
            ExtraArgs=extra_args if extra_args else None,
        )

        return {
            "filename": filename,
            "key": key,
            "bucket": S3_BUCKET_NAME,
        }

    except ClientError as error:
        raise RuntimeError(
            f"S3 이미지 수정 실패: {error}"
        ) from error


# =========================================================
# DELETE
# =========================================================

def delete_image(filename: str) -> dict:
    """
    S3 이미지 삭제
    """

    key = _build_key(filename)

    try:
        s3_client.delete_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
        )

        return {
            "filename": filename,
            "key": key,
            "deleted": True,
        }

    except ClientError as error:
        raise RuntimeError(
            f"S3 이미지 삭제 실패: {error}"
        ) from error


# =========================================================
# EXISTS
# =========================================================

def image_exists(filename: str) -> bool:
    """
    이미지 존재 여부 확인
    """

    key = _build_key(filename)

    try:
        s3_client.head_object(
            Bucket=S3_BUCKET_NAME,
            Key=key,
        )

        return True

    except ClientError as error:
        code = error.response["Error"]["Code"]

        if code in (
            "404",
            "NoSuchKey",
            "NotFound",
        ):
            return False

        raise


# =========================================================
# PRESIGNED URL
# =========================================================

def get_image_url(
    filename: str,
    expires_in: int = 3600,
) -> str:
    """
    Private S3 버킷의 이미지를 프론트에서 표시할 수 있도록
    Presigned URL 생성

    expires_in 기본값: 1시간
    """

    key = _build_key(filename)

    try:
        return s3_client.generate_presigned_url(
            ClientMethod="get_object",
            Params={
                "Bucket": S3_BUCKET_NAME,
                "Key": key,
            },
            ExpiresIn=expires_in,
        )

    except ClientError as error:
        raise RuntimeError(
            f"S3 Presigned URL 생성 실패: {error}"
        ) from error