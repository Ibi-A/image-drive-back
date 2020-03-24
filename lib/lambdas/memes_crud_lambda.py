import json
import boto3

from enum import Enum


def lambda_handler(event, _):
    pass


def generate_lambda_response(status_code: int, body):
    response = {
        "statusCode": status_code,
        "body": json.dumps(body)
    }

    return response


def process_call(http_method: str, resource: str, event):
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
        elif http_method is 'DELETE':
            result = delete_meme()


    return result


def get_memes():
    s3 = boto3.resource('s3')



    return None


def get_meme():
    return None


def post_meme():
    return None


def put_meme():
    return None


def delete_meme():
    return None