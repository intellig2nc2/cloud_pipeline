export const analyzeImage = async (
    image
) => {
    const formData =
        new FormData();

    formData.append(
        "image",
        image
    );

    const response = await fetch(
        "/api/image-rag/analyze",
        {
            method: "POST",
            body: formData,
        }
    );

    if (!response.ok) {

        const errorData =
            await response
                .json()
                .catch(() => null);

        throw new Error(
            errorData?.detail ||
            "이미지 분석 실패"
        );
    }

    return response.json();
};