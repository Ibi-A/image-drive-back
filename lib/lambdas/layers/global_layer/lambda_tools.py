import json
import boto3
import string
import random


def get_dynamodb_table_item(dynamodb_table, key_name, key_value):
    return dynamodb_table.get_item(
        Key={
            key_name: key_value
        }
    )['Item']


def get_random_id(size: int):
    random.seed()
    charset = string.digits + string.ascii_letters + '_'

    generated_id = ""

    for _ in range(0, size):
        generated_id = generated_id + \
            charset[random.randint(0, len(charset) - 1)]

    return generated_id


def extract_payload(event):
    payload = {
        "http_method": event['requestContext']['httpMethod'],
        "resource": event['resource'],
        "path": event['path'],
        "query_string_parameters": event['queryStringParameters'],
        "multi_value_query_string_parameters": event['multiValueQueryStringParameters'],
        "path_parameters": event['pathParameters'],
        "body": event['body'],
        "is_base64_encoded": event['isBase64Encoded'],
        "request_time": event['requestContext']['requestTime'],
        "headers": event['headers']
    }

    return payload


def get_generic_lambda_response(status_code: int, payload: dict):
    response = {
        "statusCode": status_code,
        "headers": {
            'Content-Type': 'application/json'
        },
        "body": json.dumps(payload)
    }

    return response


def create_presigned_url(bucket_name, object_name, expiration=3600):
    """Generate a presigned URL to share an S3 object

    :param bucket_name: string
    :param object_name: string
    :param expiration: Time in seconds for the presigned URL to remain valid
    :return: Presigned URL as string. If error, returns None.
    """

    # Generate a presigned URL for the S3 object
    s3_client = boto3.client('s3')
    try:
        response = s3_client.generate_presigned_url('get_object',
                                                    Params={'Bucket': bucket_name,
                                                            'Key': object_name},
                                                    ExpiresIn=expiration)
    except ClientError as e:
        logging.error(e)
        return None

    # The response contains the presigned URL
    return response
