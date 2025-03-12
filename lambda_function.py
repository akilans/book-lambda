import json
import logging
import boto3
from botocore.exceptions import ClientError
from datadog_lambda.metric import lambda_metric
from datadog_lambda.wrapper import datadog_lambda_wrapper
from ddtrace import tracer, patch_all

# Initialize Datadog Tracing
patch_all()  # Automatically patches all libraries like `boto3` for tracing

# Initialize logging
logger = logging.getLogger()
logger.setLevel(logging.INFO)  # You can use DEBUG for more detailed logs

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Books')

@datadog_lambda_wrapper
def lambda_handler(event, context):
    # Tracing the Lambda function
    with tracer.trace('lambda.handler', service='booksFunction'):
        logger.info(f"Received event: {json.dumps(event)}")  # Log the incoming event

        method = event['httpMethod']
        
        try:
            if method == 'POST':  # Create a new book
                body = json.loads(event['body'])
                logger.info(f"Creating new book: {body}")  # Log the book being created
                
                response = table.put_item(Item=body)
                lambda_metric("books.post_count", 1)  # Send custom metric for POST requests
                
                logger.info("Book added successfully.")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Book added successfully'})
                }

            elif method == 'GET':  # Retrieve a book by book_id
                if 'book_id' in event['queryStringParameters']:
                    book_id = event['queryStringParameters']['book_id']
                    logger.info(f"Retrieving book with book_id: {book_id}")  # Log the book retrieval

                    response = table.get_item(Key={'book_id': book_id})
                    if 'Item' in response:
                        lambda_metric("books.get_count", 1)  # Send custom metric for GET requests
                        logger.info(f"Book retrieved: {response['Item']}")
                        return {
                            'statusCode': 200,
                            'body': json.dumps(response['Item'])
                        }
                    else:
                        logger.warning(f"Book not found with book_id: {book_id}")
                        return {
                            'statusCode': 404,
                            'body': json.dumps('Book not found')
                        }

            elif method == 'PUT':  # Update book details
                book_id = event['pathParameters']['book_id']
                body = json.loads(event.get('body', '{}'))  # Use empty dict as fallback if body is None
                logger.info(f"Updating book with book_id: {book_id}, details: {body}")  # Log the update action

                update_expression = "SET"
                expression_values = {}
                for key, value in body.items():
                    update_expression += f" {key} = :{key},"
                    expression_values[f":{key}"] = value
                update_expression = update_expression.rstrip(",")  # Remove the last comma

                response = table.update_item(
                    Key={'book_id': book_id},
                    UpdateExpression=update_expression,
                    ExpressionAttributeValues=expression_values,
                    ReturnValues="UPDATED_NEW"
                )
                lambda_metric("books.put_count", 1)  # Send custom metric for PUT requests
                logger.info(f"Book updated successfully: {response.get('Attributes', {})}")
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Book updated successfully', 'updated_attributes': response.get('Attributes', {})})
                }

            elif method == 'DELETE':  # Delete a book by book_id
                book_id = event['pathParameters']['book_id']
                logger.info(f"Deleting book with book_id: {book_id}")  # Log the delete action
                
                lambda_metric("books.delete_count", 1)  # Send custom metric for DELETE requests
                response = table.delete_item(Key={'book_id': book_id})

                if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
                    logger.info(f"Book deleted successfully: {book_id}")
                    return {
                        'statusCode': 200,
                        'body': json.dumps({'message': 'Book deleted successfully'})
                    }
                else:
                    logger.warning(f"Book not found for deletion: {book_id}")
                    return {
                        'statusCode': 404,
                        'body': json.dumps('Book not found')
                    }

        except Exception as e:
            logger.error(f"An error occurred: {str(e)}")  # Log the error
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'An error occurred', 'error': str(e)})
            }
