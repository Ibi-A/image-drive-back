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