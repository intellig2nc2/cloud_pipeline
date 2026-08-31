pipeline {
    agent any

    stages {
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