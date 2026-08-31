import {
    useState,
} from "react";

import styled from "styled-components";

import {
    useQueryImage,
} from "../query/imageRagQuery";


const ImageQuestion = () => {
    const [question, setQuestion] =
        useState("");

    const queryMutation =
        useQueryImage();


    const handleQuery = () => {
        const value =
            question.trim();

        if (!value) {
            alert(
                "질문을 입력해주세요."
            );

            return;
        }

        queryMutation.mutate(
            value
        );
    };


    const handleKeyDown = (
        event
    ) => {
        if (
            event.key === "Enter"
        ) {
            handleQuery();
        }
    };


    return (
        <Container>

            <Title>
                음식 찾기
            </Title>

            <Description>
                images 폴더와 등록된 이미지에서
                가장 비슷한 음식을 찾아줍니다.
            </Description>

            <Input
                value={question}
                onChange={(event) =>
                    setQuestion(
                        event.target.value
                    )
                }
                onKeyDown={
                    handleKeyDown
                }
                placeholder="예: 감자가 올라간 피자 찾아줘"
            />

            <Button
                onClick={
                    handleQuery
                }
                disabled={
                    queryMutation.isPending
                }
            >
                {queryMutation.isPending
                    ? "찾는 중..."
                    : "음식 찾기"}
            </Button>

            {queryMutation.isPending && (
                <Message>
                    이미지들을 비교하고 있습니다...
                </Message>
            )}

            {queryMutation.isError && (
                <ErrorMessage>
                    {
                        queryMutation
                            .error
                            .message
                    }
                </ErrorMessage>
            )}

            {queryMutation.data && (
                <ResultBox>

                    <ResultTitle>
                        검색 결과
                    </ResultTitle>

                    {queryMutation.data.image_url && (
                        <ResultImage
                            src={
                                queryMutation
                                    .data
                                    .image_url
                            }
                            alt={
                                queryMutation
                                    .data
                                    .matched_filename ||
                                "검색된 음식"
                            }
                        />
                    )}

                    <ImageName>
                        {
                            queryMutation
                                .data
                                .matched_filename
                        }
                    </ImageName>

                    <Answer>
                        {
                            queryMutation
                                .data
                                .answer
                        }
                    </Answer>

                </ResultBox>
            )}

        </Container>
    );
};


export default ImageQuestion;


const Container = styled.div`
  display: flex;
  flex-direction: column;
  gap: 16px;

  padding: 24px;

  border: 1px solid #dddddd;
  border-radius: 12px;
`;


const Title = styled.h2`
  margin: 0;
`;


const Description = styled.p`
  margin: 0;

  color: #666666;
  line-height: 1.5;
`;


const Input = styled.input`
  padding: 12px;

  border: 1px solid #cccccc;
  border-radius: 8px;

  font-size: 15px;
`;


const Button = styled.button`
  padding: 12px 16px;

  border: none;
  border-radius: 8px;

  cursor: pointer;

  &:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
`;


const Message = styled.p`
  margin: 0;
`;


const ErrorMessage = styled.p`
  margin: 0;
`;


const ResultBox = styled.div`
  padding: 16px;

  border-radius: 10px;

  background: #f5f5f5;
`;


const ResultTitle = styled.h3`
  margin-top: 0;
  margin-bottom: 14px;
`;


const ResultImage = styled.img`
  display: block;

  width: 100%;
  max-height: 420px;

  object-fit: contain;

  margin-bottom: 12px;

  border-radius: 10px;
`;


const ImageName = styled.p`
  margin: 0 0 12px;

  font-size: 13px;
  color: #777777;
`;


const Answer = styled.p`
  margin: 0;

  line-height: 1.7;
  font-size: 16px;
`;