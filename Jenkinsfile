pipeline {
    agent any

    environment {
        AWS_REGION = 'us-east-1'  // Change to your AWS region
        LAMBDA_FUNCTION_NAME = 'booksFunction'  // Lambda function name
    }

    stages {

        stage('Deploy Lambda Function') {
            steps {
                script {
                    // Package and deploy Lambda function using AWS CLI or Serverless framework
                    sh '''
                    zip -r lambda_function.zip books.py
                    aws lambda update-function-code --function-name $LAMBDA_FUNCTION_NAME --zip-file fileb://lambda_function.zip --region $AWS_REGION
                    '''
                }
            }
        }
    }

    post {
        success {
            echo 'Lambda function deployed successfully!'
        }
        failure {
            echo 'Lambda deployment failed.'
        }
    }
}
