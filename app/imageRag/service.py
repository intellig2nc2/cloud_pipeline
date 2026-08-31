import base64
import math
from pathlib import Path
from urllib.parse import quote

import torch

from fastapi import UploadFile

from openai import OpenAI

from PIL import Image

from transformers import (
    CLIPModel,
    CLIPProcessor,
)

from config import OPENAI_API_KEY


# ==================================================
# OpenAI
# ==================================================

client = OpenAI(
    api_key=OPENAI_API_KEY
)


# ==================================================
# 경로
# ==================================================

# backend/app
APP_DIR = (
    Path(__file__)
    .resolve()
    .parents[1]
)

# backend/app/images
IMAGES_DIR = (
    APP_DIR
    / "images"
)


# ==================================================
# CLIP
# ==================================================

DEVICE = (
    "cuda"
    if torch.cuda.is_available()
    else "cpu"
)


print(
    f"[Image RAG] CLIP DEVICE: {DEVICE}"
)


clip_model = (
    CLIPModel.from_pretrained(
        "openai/clip-vit-base-patch32"
    )
    .to(DEVICE)
)


clip_processor = (
    CLIPProcessor.from_pretrained(
        "openai/clip-vit-base-patch32"
    )
)


clip_model.eval()


# ==================================================
# 폴더 이미지 Vector Store
# ==================================================

folder_image_store = []

folder_images_loaded = False


# ==================================================
# 이미지 URL
# ==================================================

def make_image_url(
    filename: str,
) -> str:

    encoded_filename = quote(
        filename
    )

    return (
        f"/images/{encoded_filename}"
    )


# ==================================================
# 이미지 → CLIP Embedding
# ==================================================

def create_image_embedding(
    image: Image.Image,
) -> list[float]:

    image = image.convert(
        "RGB"
    )

    inputs = clip_processor(
        images=image,
        return_tensors="pt",
    )

    pixel_values = (
        inputs["pixel_values"]
        .to(DEVICE)
    )

    with torch.no_grad():

        features = (
            clip_model
            .get_image_features(
                pixel_values=pixel_values
            )
        )

    # L2 Normalize
    features = (
        features
        / features.norm(
            p=2,
            dim=-1,
            keepdim=True,
        )
    )

    return (
        features[0]
        .detach()
        .cpu()
        .tolist()
    )


# ==================================================
# Cosine Similarity
# ==================================================

def cosine_similarity(
    vector_a: list[float],
    vector_b: list[float],
) -> float:

    dot_product = sum(
        a * b
        for a, b in zip(
            vector_a,
            vector_b,
        )
    )

    magnitude_a = math.sqrt(
        sum(
            value * value
            for value in vector_a
        )
    )

    magnitude_b = math.sqrt(
        sum(
            value * value
            for value in vector_b
        )
    )

    if (
        magnitude_a == 0
        or magnitude_b == 0
    ):
        return 0.0

    return (
        dot_product
        / (
            magnitude_a
            * magnitude_b
        )
    )


# ==================================================
# backend/app/images
# 기준 이미지 Embedding 생성
# ==================================================

def load_folder_images():

    global folder_images_loaded

    if folder_images_loaded:
        return

    folder_image_store.clear()

    if not IMAGES_DIR.exists():

        print(
            f"[Image RAG] "
            f"images 폴더 없음: "
            f"{IMAGES_DIR}"
        )

        folder_images_loaded = True

        return

    allowed_extensions = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp",
    }

    image_paths = [
        path
        for path in IMAGES_DIR.iterdir()
        if (
            path.is_file()
            and path.suffix.lower()
            in allowed_extensions
        )
    ]

    print(
        f"[Image RAG] "
        f"기준 이미지 "
        f"{len(image_paths)}개 로딩"
    )

    for image_path in image_paths:

        try:

            print(
                f"[Image RAG] "
                f"Embedding 생성: "
                f"{image_path.name}"
            )

            with Image.open(
                image_path
            ) as image:

                embedding = (
                    create_image_embedding(
                        image
                    )
                )

            folder_image_store.append(
                {
                    "filename":
                        image_path.name,

                    "path":
                        image_path,

                    "image_url":
                        make_image_url(
                            image_path.name
                        ),

                    "embedding":
                        embedding,
                }
            )

        except Exception as error:

            print(
                f"[Image RAG] "
                f"{image_path.name} "
                f"처리 실패: "
                f"{error}"
            )

    folder_images_loaded = True

    print(
        f"[Image RAG] "
        f"Vector Store 완료: "
        f"{len(folder_image_store)}개"
    )


# ==================================================
# 입력 이미지와 폴더 이미지 직접 비교
# ==================================================

def search_similar_images(
    uploaded_image: Image.Image,
    top_k: int = 3,
) -> list[dict]:

    load_folder_images()

    if not folder_image_store:
        return []

    # 입력 이미지 자체의 CLIP Vector
    query_embedding = (
        create_image_embedding(
            uploaded_image
        )
    )

    results = []

    for item in folder_image_store:

        score = cosine_similarity(
            query_embedding,
            item["embedding"],
        )

        results.append(
            {
                **item,
                "score": score,
            }
        )

        print(
            f"[Image RAG] "
            f"{item['filename']} "
            f"score={score:.4f}"
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    top_results = (
        results[:top_k]
    )

    print(
        "\n[Image RAG] TOP RESULTS"
    )

    for result in top_results:

        print(
            f"{result['filename']} "
            f"{result['score']:.4f}"
        )

    return top_results


# ==================================================
# 파일 → Base64
# GPT Vision용
# ==================================================

def file_to_data_url(
    image_path: Path,
) -> str:

    image_bytes = (
        image_path.read_bytes()
    )

    extension = (
        image_path
        .suffix
        .lower()
    )

    content_types = {
        ".jpg": "image/jpeg",
        ".jpeg": "image/jpeg",
        ".png": "image/png",
        ".webp": "image/webp",
    }

    content_type = (
        content_types.get(
            extension,
            "image/jpeg",
        )
    )

    encoded = (
        base64
        .b64encode(
            image_bytes
        )
        .decode("utf-8")
    )

    return (
        f"data:{content_type};"
        f"base64,{encoded}"
    )


# ==================================================
# UploadFile → Base64
# ==================================================

def bytes_to_data_url(
    image_bytes: bytes,
    content_type: str,
) -> str:

    encoded = (
        base64
        .b64encode(
            image_bytes
        )
        .decode("utf-8")
    )

    return (
        f"data:{content_type};"
        f"base64,{encoded}"
    )


# ==================================================
# 최종 음식 판별
# ==================================================

def generate_food_answer(
    uploaded_bytes: bytes,
    uploaded_content_type: str,
    similar_images: list[dict],
) -> str:

    content = [
        {
            "type": "input_text",
            "text": (
                "첫 번째 이미지는 사용자가 입력한 음식 사진이다. "
                "그 뒤의 이미지들은 이미지 임베딩 검색으로 찾은 "
                "가장 유사한 기준 음식 사진들이다. "
                "이 이미지들을 종합해서 첫 번째 사진의 음식이 "
                "무엇인지 추정해라. "
                "가장 가능성이 높은 음식 이름을 먼저 말하고 "
                "간단한 특징을 한 문장으로 설명해라. "
                "답변은 한국어로 최대 2문장만 작성해라. "
                "분석 과정, 메타데이터, 태그, JSON은 출력하지 마라."
            ),
        },

        # 첫 번째 = 사용자 입력 이미지
        {
            "type": "input_image",
            "image_url":
                bytes_to_data_url(
                    uploaded_bytes,
                    uploaded_content_type,
                ),
        },
    ]

    # Top-K 기준 이미지 추가
    for item in similar_images:

        content.append(
            {
                "type": "input_image",
                "image_url":
                    file_to_data_url(
                        item["path"]
                    ),
            }
        )

    response = (
        client.responses.create(
            model="gpt-5-mini",
            input=[
                {
                    "role": "user",
                    "content": content,
                }
            ],
        )
    )

    return (
        response
        .output_text
        .strip()
    )


# ==================================================
# API Service
# ==================================================

async def analyze_image(
    image: UploadFile,
) -> dict:

    if not image.filename:

        raise ValueError(
            "이미지를 선택해주세요."
        )

    image_bytes = (
        await image.read()
    )

    if not image_bytes:

        raise ValueError(
            "빈 이미지 파일입니다."
        )

    # ----------------------------------------------
    # PIL로 입력 이미지 열기
    # ----------------------------------------------

    import io

    try:

        uploaded_image = (
            Image.open(
                io.BytesIO(
                    image_bytes
                )
            )
            .convert("RGB")
        )

    except Exception:

        raise ValueError(
            "올바른 이미지 파일이 아닙니다."
        )

    # ----------------------------------------------
    # 1. CLIP 이미지 직접 비교
    # ----------------------------------------------

    similar_images = (
        search_similar_images(
            uploaded_image,
            top_k=3,
        )
    )

    if not similar_images:

        return {
            "answer":
                "비교할 기준 이미지가 없습니다.",

            "similar_images": [],
        }

    # ----------------------------------------------
    # 2. Top-K 기반 음식 이름 판별
    # ----------------------------------------------

    content_type = (
        image.content_type
        or "image/jpeg"
    )

    answer = generate_food_answer(
        uploaded_bytes=image_bytes,
        uploaded_content_type=
            content_type,
        similar_images=
            similar_images,
    )

    # ----------------------------------------------
    # 3. Frontend Response
    # ----------------------------------------------

    return {
        "answer": answer,

        "similar_images": [
            {
                "filename":
                    item["filename"],

                "image_url":
                    item["image_url"],

                "score":
                    item["score"],
            }

            for item
            in similar_images
        ],
    }