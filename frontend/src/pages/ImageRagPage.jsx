import styled from "styled-components";

import ImageUploader from "../components/ImageUploader";


const ImageRagPage = () => {

    return (
        <Container>

            <Title>
                Food Image RAG
            </Title>

            <ImageUploader />

        </Container>
    );
};


export default ImageRagPage;


const Container = styled.main`
  width: 100%;
  max-width: 900px;

  margin: 0 auto;
  padding: 40px 20px;
`;


const Title = styled.h1`
  margin-bottom: 24px;
`;