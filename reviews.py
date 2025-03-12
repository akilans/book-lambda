import json
import boto3
from decimal import Decimal
from botocore.exceptions import ClientError
# Initialize DynamoDB resource
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table('Reviews')
def decimal_to_float(obj):
    """Recursively convert Decimal objects to float."""
    if isinstance(obj, Decimal):
        return float(obj)
    elif isinstance(obj, dict):
        return {k: decimal_to_float(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [decimal_to_float(i) for i in obj]
    return obj

def lambda_handler(event, context):
    method = event['httpMethod']
    if method == 'POST':  # Create a new review
        body = json.loads(event['body'])
        response = table.put_item(Item=body)
        return {
            'statusCode': 200,
            'body': json.dumps({'message': 'Review added successfully'})
        }
    if method == 'GET':
        # Check if 'review_id' and 'book_id' are in queryStringParameters
        if 'review_id' in event['queryStringParameters'] and 'book_id' in event['queryStringParameters']:
            review_id = event['queryStringParameters']['review_id']
            book_id = event['queryStringParameters']['book_id']
            response = table.get_item(Key={'review_id': review_id, 'book_id': book_id})
            if 'Item' in response:
                # Convert any Decimal values in the response to float
                response_item = decimal_to_float(response['Item'])
                return {
                    'statusCode': 200,
                    'body': json.dumps(response_item)
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps({'error': 'Review not found'})
                }
        
        # If 'review_id' and 'book_id' are not in query parameters, retrieve all reviews
        elif 'review_id' not in event['queryStringParameters'] and 'book_id' not in event['queryStringParameters']:
            try:
                # Scan the DynamoDB table to get all items (reviews)
                response = table.scan()
                if 'Items' in response and len(response['Items']) > 0:
                    # Convert any Decimal values in the response to float
                    all_reviews = [decimal_to_float(item) for item in response['Items']]
                    return {
                        'statusCode': 200,
                        'body': json.dumps(all_reviews)
                    }
                else:
                    return {
                        'statusCode': 404,
                        'body': json.dumps({'error': 'No reviews found'})
                    }
            except ClientError as e:
                return {
                    'statusCode': 500,
                    'body': json.dumps({'message': 'Error fetching reviews', 'error': str(e)})
                }
        
        else:
            return {
                'statusCode': 400,
                'body': json.dumps({'error': 'Missing required query parameters: review_id, book_id'})
            }
    elif method == 'PUT':  # Update review details
        review_id = event['queryStringParameters']['review_id']
        body = json.loads(event['body'])
        try:
            # Update attributes of the review
            update_expression = "SET"
            expression_values = {}
            for key, value in body.items():
                update_expression += f" {key} = :{key},"
                expression_values[f":{key}"] = value
            update_expression = update_expression.rstrip(",")  # Remove the last comma
            response = table.update_item(
                Key={'review_id': review_id},
                UpdateExpression=update_expression,
                ExpressionAttributeValues=expression_values,
                ReturnValues="UPDATED_NEW"
            )
            return {
                'statusCode': 200,
                'body': json.dumps({'message': 'Review updated successfully', 'updated_attributes': response['Attributes']})
            }
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Error updating review', 'error': str(e)})
            }
    elif method == 'DELETE':  # Delete a review by review_id
        review_id = event['queryStringParameters']['review_id']
        try:
            response = table.delete_item(Key={'review_id': review_id})
            if response.get('ResponseMetadata', {}).get('HTTPStatusCode') == 200:
                return {
                    'statusCode': 200,
                    'body': json.dumps({'message': 'Review deleted successfully'})
                }
            else:
                return {
                    'statusCode': 404,
                    'body': json.dumps('Review not found')
                }
        except ClientError as e:
            return {
                'statusCode': 500,
                'body': json.dumps({'message': 'Error deleting review', 'error': str(e)})
            }
