import {
    useEffect,
    useState,
} from "react";

import styled from "styled-components";

import {
    useAnalyzeImage,
} from "../query/imageRagQuery";


const ImageUploader = () => {

    const [image, setImage] =
        useState(null);

    const [preview, setPreview] =
        useState(null);

    const analyzeMutation =
        useAnalyzeImage();


    useEffect(() => {

        if (!image) {
            setPreview(null);
            return;
        }

        const url =
            URL.createObjectURL(
                image
            );

        setPreview(url);

        return () => {
            URL.revokeObjectURL(
                url
            );
        };

    }, [image]);


    const handleFileChange = (
        event
    ) => {

        const file =
            event.target
                .files?.[0];

        if (!file) {
            return;
        }

        setImage(file);

        analyzeMutation.reset();
    };


    const handleAnalyze = () => {

        if (!image) {

            alert(
                "이미지를 선택해주세요."
            );

            return;
        }

        analyzeMutation.mutate(
            image
        );
    };


    return (
        <Container>

            <Title>
                음식 이미지 분석
            </Title>

            <Description>
                사진을 입력하면 기준 이미지들과
                비교해서 어떤 음식인지 찾아줍니다.
            </Description>

            <FileInput
                type="file"
                accept="image/*"
                onChange={
                    handleFileChange
                }
            />

            {preview && (
                <PreviewSection>

                    <SectionTitle>
                        입력 이미지
                    </SectionTitle>

                    <PreviewImage
                        src={preview}
                        alt="입력 이미지"
                    />

                </PreviewSection>
            )}

            <AnalyzeButton
                onClick={
                    handleAnalyze
                }
                disabled={
                    analyzeMutation
                        .isPending
                }
            >

                {analyzeMutation.isPending
                    ? "이미지 비교 중..."
                    : "음식 분석하기"}

            </AnalyzeButton>


            {analyzeMutation.isError && (

                <ErrorMessage>
                    {
                        analyzeMutation
                            .error
                            .message
                    }
                </ErrorMessage>

            )}


            {analyzeMutation.data && (

                <ResultSection>

                    <ResultTitle>
                        분석 결과
                    </ResultTitle>

                    <Answer>
                        {
                            analyzeMutation
                                .data
                                .answer
                        }
                    </Answer>


                    <SimilarTitle>
                        유사 이미지
                    </SimilarTitle>


                    <SimilarGrid>

                        {
                            analyzeMutation
                                .data
                                .similar_images
                                .map(
                                    (
                                        item,
                                        index
                                    ) => (

                                        <SimilarCard
                                            key={
                                                item.filename
                                            }
                                        >

                                            <Rank>
                                                TOP {index + 1}
                                            </Rank>

                                            <SimilarImage
                                                src={
                                                    item.image_url
                                                }
                                                alt={
                                                    item.filename
                                                }
                                            />

                                            <Filename>
                                                {
                                                    item.filename
                                                }
                                            </Filename>

                                            <Score>
                                                유사도{" "}
                                                {(
                                                    item.score
                                                    * 100
                                                ).toFixed(1)}
                                                %
                                            </Score>

                                        </SimilarCard>

                                    )
                                )
                        }

                    </SimilarGrid>

                </ResultSection>

            )}

        </Container>
    );
};


export default ImageUploader;


const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 18px;

  padding: 24px;

  border: 1px solid #ddd;
  border-radius: 12px;
`;


const Title = styled.h2`
  margin: 0;
`;


const Description = styled.p`
  margin: 0;
  color: #666;
`;


const FileInput = styled.input``;


const PreviewSection = styled.div`
  display: flex;
  flex-direction: column;
  gap: 10px;
`;


const SectionTitle = styled.h3`
  margin: 0;
`;


const PreviewImage = styled.img`
  width: 100%;
  max-height: 400px;

  object-fit: contain;

  border-radius: 10px;
`;


const AnalyzeButton = styled.button`
  padding: 13px;

  border: none;
  border-radius: 8px;

  cursor: pointer;

  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
`;


const ErrorMessage = styled.p`
  margin: 0;
`;


const ResultSection = styled.div`
  margin-top: 10px;

  padding: 20px;

  background: #f5f5f5;

  border-radius: 10px;
`;


const ResultTitle = styled.h2`
  margin-top: 0;
`;


const Answer = styled.p`
  font-size: 17px;
  line-height: 1.7;
`;


const SimilarTitle = styled.h3`
  margin-top: 24px;
`;


const SimilarGrid = styled.div`
  display: grid;

  grid-template-columns:
    repeat(3, 1fr);

  gap: 14px;

  @media (
    max-width: 700px
  ) {
    grid-template-columns:
      1fr;
  }
`;


const SimilarCard = styled.div`
  padding: 10px;

  background: white;

  border-radius: 10px;
`;


const Rank = styled.strong`
  display: block;

  margin-bottom: 8px;
`;


const SimilarImage = styled.img`
  width: 100%;
  height: 160px;

  object-fit: contain;

  border-radius: 8px;
`;


const Filename = styled.p`
  margin:
    8px 0 4px;

  font-size: 13px;

  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
`;


const Score = styled.p`
  margin: 0;

  font-size: 13px;
  color: #666;
`;