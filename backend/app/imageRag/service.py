import base64
from io import BytesIO

import torch
from fastapi import UploadFile
from openai import OpenAI
from PIL import Image
from transformers import CLIPModel, CLIPProcessor

from app.storage.s3 import (
    list_images,
    get_image,
    get_image_url,
)
from config import OPENAI_API_KEY


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"

client = OpenAI(api_key=OPENAI_API_KEY)

clip_model = CLIPModel.from_pretrained(
    "openai/clip-vit-base-patch32"
).to(DEVICE)

clip_processor = CLIPProcessor.from_pretrained(
    "openai/clip-vit-base-patch32"
)


def create_image_embedding(image: Image.Image) -> torch.Tensor:
    image = image.convert("RGB")

    inputs = clip_processor(
        images=image,
        return_tensors="pt",
    )

    pixel_values = inputs["pixel_values"].to(DEVICE)

    with torch.no_grad():
        vision_output = clip_model.vision_model(
            pixel_values=pixel_values
        )

        pooled_output = vision_output.pooler_output

        embedding = clip_model.visual_projection(
            pooled_output
        )

    embedding = embedding / embedding.norm(
        p=2,
        dim=-1,
        keepdim=True,
    )

    return embedding.squeeze(0).cpu()


def load_reference_images() -> list[dict]:
    references = []

    s3_images = list_images()

    for item in s3_images:
        filename = item["filename"]

        try:
            image_data = get_image(filename)

            image = Image.open(
                BytesIO(image_data["body"])
            ).convert("RGB")

            embedding = create_image_embedding(image)

            references.append(
                {
                    "filename": filename,
                    "image": image,
                    "embedding": embedding,
                }
            )

        except Exception as error:
            print(
                f"[Image RAG] 기준 이미지 로딩 실패 "
                f"{filename}: {error}"
            )

    return references


def search_similar_images(
    uploaded_image: Image.Image,
    top_k: int = 3,
) -> list[dict]:
    uploaded_embedding = create_image_embedding(
        uploaded_image
    )

    reference_images = load_reference_images()

    if not reference_images:
        return []

    results = []

    for reference in reference_images:
        score = torch.nn.functional.cosine_similarity(
            uploaded_embedding.unsqueeze(0),
            reference["embedding"].unsqueeze(0),
        ).item()

        results.append(
            {
                "filename": reference["filename"],
                "image": reference["image"],
                "score": score,
            }
        )

    results.sort(
        key=lambda item: item["score"],
        reverse=True,
    )

    return results[:top_k]


def image_to_data_url(image: Image.Image) -> str:
    buffer = BytesIO()

    image.convert("RGB").save(
        buffer,
        format="JPEG",
    )

    encoded = base64.b64encode(
        buffer.getvalue()
    ).decode("utf-8")

    return f"data:image/jpeg;base64,{encoded}"


def generate_food_answer(
    uploaded_image: Image.Image,
    similar_images: list[dict],
) -> str:
    content = [
        {
            "type": "input_text",
            "text": (
                "첫 번째 이미지는 사용자가 업로드한 음식 이미지입니다. "
                "그 뒤 이미지들은 이미지 유사도 검색으로 찾은 "
                "기준 음식 이미지입니다. "
                "이들을 참고해서 첫 번째 이미지의 음식 이름을 "
                "한국어로 판단하고 간단한 설명을 해주세요. "
                "최대 2문장으로 답해주세요."
            ),
        },
        {
            "type": "input_image",
            "image_url": image_to_data_url(
                uploaded_image
            ),
        },
    ]

    for item in similar_images:
        content.append(
            {
                "type": "input_image",
                "image_url": image_to_data_url(
                    item["image"]
                ),
            }
        )

    response = client.responses.create(
        model="gpt-5-mini",
        input=[
            {
                "role": "user",
                "content": content,
            }
        ],
    )

    return response.output_text


async def analyze_image(
    image: UploadFile,
) -> dict:
    """
    이미지 분석 API의 최종 진입점.

    업로드 이미지
    → CLIP embedding
    → S3 기준 이미지 직접 비교
    → Top 3
    → GPT 음식 분석
    """

    if not image.content_type:
        raise ValueError(
            "이미지 파일을 업로드해주세요."
        )

    if not image.content_type.startswith("image/"):
        raise ValueError(
            "이미지 파일만 업로드할 수 있습니다."
        )

    image_bytes = await image.read()

    if not image_bytes:
        raise ValueError(
            "빈 이미지 파일입니다."
        )

    try:
        uploaded_image = Image.open(
            BytesIO(image_bytes)
        ).convert("RGB")

    except Exception as error:
        raise ValueError(
            "이미지를 읽을 수 없습니다."
        ) from error

    similar_images = search_similar_images(
        uploaded_image,
        top_k=3,
    )

    if not similar_images:
        return {
            "answer": "비교할 기준 이미지가 없습니다.",
            "similar_images": [],
        }

    answer = generate_food_answer(
        uploaded_image,
        similar_images,
    )

    result_images = []

    for item in similar_images:
        result_images.append(
            {
                "filename": item["filename"],
                "image_url": get_image_url(
                    item["filename"]
                ),
                "score": round(
                    item["score"],
                    4,
                ),
            }
        )

    return {
        "answer": answer,
        "similar_images": result_images,
    }