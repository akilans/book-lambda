#added comment
import json
import boto3
from botocore.exceptions import ClientError

# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Books')

def lambda_handler(event, context):
    method = event['httpMethod']

    if method == 'POST':  # Create a new book
        body = json.loads(event['body'])
        response = table.put_item(Item=body)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Book added successfully'})
        }

    elif method == 'GET':
    # Check if 'book_id' query parameter is provided
        if 'book_id' in event['queryStringParameters']:
            # Retrieve a specific book by book_id
            book_id = event['queryStringParameters']['book_id']
            response = table.get_item(Key={'book_id': book_id})

            if 'Item' in response:
                return {
                    'statusCode': 200,
                    'body': json.dumps(response['Item'])
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps('Book not found')
                }
        else:
            # Retrieve all books in the table
            response = table.scan()

            if 'Items' in response and len(response['Items']) > 0:
                return {
                    'statusCode': 200,
                    'body': json.dumps(response['Items'])
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps('No books found')
                }

    elif method == 'PUT':  # Update book details
        book_id = event['queryStringParameters']['book_id']
        body = json.loads(event['body'])

        try:
            # Update attributes of the book
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

            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Book updated successfully', 'updated_attributes': response['Attributes']})
            }

        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Error updating book', 'error': str(e)})
            }

    elif method == 'DELETE':  # Delete a book by book_id
        book_id = event['queryStringParameters']['book_id']

        try:
            response = table.delete_item(Key={'book_id': book_id})
            if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Book deleted successfully'})
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps('Book not found')
                }

        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Error deleting book', 'error': str(e)})
            }
