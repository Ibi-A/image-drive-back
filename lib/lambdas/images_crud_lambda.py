import json
import boto3
import os

from enum import Enum
from base64 import b64encode


def lambda_handler(event, _):
    # payload = extract_payload(event)
    # response = process_call(payload['http_method'], payload['resource'])
    response = {
        "statusCode": 302,
        "headers": {
            "Location": create_presigned_url(os.environ['memes_s3_bucket_name'], "dab.png")
        }
    }

    return response

def extract_payload(event):
    payload = {
        "http_method": event['requestContext']['httpMethod'],
        "resource": event['resource'],
        "path": event['path'],
        "query_string_parameters": event['queryStringParameters'],
        "multi_value_query_string_parameters": event['multiValueQueryStringParameters'],
        "path_parameters": event['parathParameters'],
        "body": event['body'],
        "is_base64_encoded": event['isBase64Encoded'],
        "request_time": event['requestContext']['requestTime']
    }

    return payload


def generate_lambda_response(status_code: int, payload: dict):
    response = {
        "statusCode": status_code,
        "body": json.dumps(payload)
    }

    return response


def process_call(http_method: str, resource: str, payload: dict):
    result = None

    if resource is '/memes':
        if http_method is 'GET':
            result = get_memes()
        elif http_method is 'POST':
            result = post_meme()
    elif resource is '/memes/{meme-name}':
        if http_method is 'GET':
            result = get_meme()
        elif http_method is 'PUT':
            result = put_meme()
        elif http_method is 'PATCH':
            result = patch_meme()
        elif http_method is 'DELETE':
            result = delete_meme()

    return result


def get_content_type(filename: str):
    if str.lower(get_file_extension(filename)) in ['png']:
        pass
    elif str.lower(get_file_extension(filename)) in ['jpg', 'jpeg']:
        pass


def get_memes():
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['memes_s3_bucket_name'])

    payload = {}


    return None


def get_meme(meme_name: str):
    # fetch the meme information from the DynamoDB table
    dynamodb = boto3.resource('dynamodb')

    table = dynamodb.Table(os.environ['memes_dynamodb_information_table'])

    response = table.get_item(
        Key={
            'name': meme_name
        }
    )

    item = response['Item']

    return create_presigned_url(os.environ['memes_s3_bucket_name'], item['uri'])


def post_meme():
    return None


def put_meme():
    return None


def patch_meme():
    return None


def delete_meme():
    return None



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
