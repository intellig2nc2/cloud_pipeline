from fastapi import (
    APIRouter,
    File,
    HTTPException,
    UploadFile,
)

from app.imageRag.schema import (
    ImageAnalyzeResponse,
)

from app.imageRag.service import (
    analyze_image,
)


router = APIRouter(
    prefix="/api/image-rag",
    tags=["Image RAG"],
)


@router.post(
    "/analyze",
    response_model=ImageAnalyzeResponse,
)
async def image_rag_analyze(
    image: UploadFile = File(...),
):

    try:

        result = await analyze_image(
            image
        )

        return ImageAnalyzeResponse(
            **result
        )

    except ValueError as error:

        raise HTTPException(
            status_code=400,
            detail=str(error),
        )

    except Exception as error:

        print(
            f"[Image RAG] 오류: "
            f"{error}"
        )

        raise HTTPException(
            status_code=500,
            detail=(
                "이미지 분석 중 "
                "오류가 발생했습니다."
            ),
        )