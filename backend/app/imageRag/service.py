from io import BytesIO

from PIL import Image

from app.storage.s3 import list_images, get_image


def load_reference_images():
    references = []

    for item in list_images():
        filename = item["filename"]

        image_data = get_image(filename)

        image = Image.open(
            BytesIO(image_data["body"])
        ).convert("RGB")

        references.append(
            {
                "filename": filename,
                "image": image,
            }
        )

    return references