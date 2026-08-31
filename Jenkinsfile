pipeline {
    agent any

    environment {
        GITHUB_REPO = 'YOUR_GITHUB_REPO_URL'
        GITHUB_BRANCH = 'main'
    }

    stages {
        stage('Checkout') {
            steps {
                git branch: "${GITHUB_BRANCH}",
                    url: "${GITHUB_REPO}"
            }
        }

        stage('Create .env') {
            steps {
                withCredentials([
                    file(credentialsId: 'image-rag-env', variable: 'ENV_FILE')
                ]) {
                    sh 'cp "$ENV_FILE" .env'
                }
            }
        }

        stage('Docker Build') {
            steps {
                sh 'docker compose build'
            }
        }

        stage('Deploy') {
            steps {
                sh '''
                    docker compose down || true
                    docker compose up -d --remove-orphans
                '''
            }
        }
    }

    post {
        success {
            echo '배포 성공'
        }

        failure {
            echo '배포 실패'
        }
    }
}