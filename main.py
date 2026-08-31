from pathlib import Path

from fastapi import FastAPI

from fastapi.middleware.cors import (
    CORSMiddleware,
)

from fastapi.staticfiles import (
    StaticFiles,
)

from app.imageRag.web import (
    router as image_rag_router,
)


app = FastAPI(
    title="Food Image RAG"
)


app.add_middleware(
    CORSMiddleware,

    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],

    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(
    image_rag_router
)


BASE_DIR = (
    Path(__file__)
    .resolve()
    .parent
)

IMAGES_DIR = (
    BASE_DIR
    / "app"
    / "images"
)

IMAGES_DIR.mkdir(
    parents=True,
    exist_ok=True,
)


app.mount(
    "/images",

    StaticFiles(
        directory=str(
            IMAGES_DIR
        )
    ),

    name="images",
)


@app.get("/")
def root():

    return {
        "message":
            "Food Image RAG running"
    }