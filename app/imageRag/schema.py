from pydantic import BaseModel


class SimilarImage(BaseModel):
    filename: str
    image_url: str
    score: float


class ImageAnalyzeResponse(BaseModel):
    answer: str
    similar_images: list[SimilarImage]