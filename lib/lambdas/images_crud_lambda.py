import json
import boto3
import os
import string
import random

from enum import Enum
from base64 import b64encode, b64decode

from layers.global_layer.lambda_tools import extract_payload, create_presigned_url


class Image:

    s3_bucket = None
    dynamodb_table = None

    image_id: str = None
    image_name: str = None
    image_format: str = None
    image_s3_key: str = None

    encoded_b64_image = None

    def get_random_id(self, size: int):
        random.seed()
        charset = string.digits + string.ascii_letters + '_'

        generated_id = ""

        for _ in range(0, size):
            generated_id = generated_id + charset[random.randint(0, len(charset) - 1)]

        return generated_id

    def __init__(self, s3_bucket, dynamodb_table, image_id=None, image_name=None, image_format=None, encoded_b64_image=None):
        self.s3_bucket = s3_bucket
        self.dynamodb_table = dynamodb_table

        if image_id is not None:
            self.image_id = image_id
            image_info = self.dynamodb_table.get_item(
                Key={
                    'id': image_id
                }
            )['Item']

            self.image_name = image_info['name']
            self.image_format = image_info['format']
            self.image_s3_key = image_info['s3_key']

        elif (image_name and image_format and encoded_b64_image) is not None:
            self.image_id = self.get_random_id(8)
            self.image_name = image_name
            self.image_format = image_format.upper()
            self.image_s3_key = f'{self.image_id}.{self.image_format.lower()}'
            self.encoded_b64_image = encoded_b64_image

    def get_image_http_payload(self):
        redirect_url = create_presigned_url(
            self.s3_bucket.name, self.image_s3_key)

        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": 'application/json'
            },
            "body": json.dumps({
                "id": self.image_id,
                "imageName": self.image_name,
                "imageFormat": self.image_format,
                "uri": redirect_url
            })
        }

    def save_image(self):
        decoded_b64_image = b64decode(self.encoded_b64_image)

        self.s3_bucket.put_object(
            Key=f"{self.image_s3_key}", Body=decoded_b64_image, ACL='public-read')

        self.dynamodb_table.put_item(
            Item={
                'id': self.image_id,
                'name': self.image_name,
                'format': self.image_format,
                's3_key': self.image_s3_key
            }
        )

        response = {
            "statusCode": 201,
            "headers": {
                "Content-Type": 'application/json'
            },
            "body": json.dumps({
                "id": self.image_id,
                "name": self.image_name,
                "format": self.image_format
            })
        }

        return response


def lambda_handler(event, _):
    payload = extract_payload(event)
    response = process_call(payload)

    return response


def process_call(payload: dict):
    calls = {
        "/images": {
            "GET": get_images,
            "POST": post_image
        },
        "/images/{image-id}": {
            "GET": get_image,
            "PUT": put_image,
            "PATCH": patch_image,
            "DELETE": delete_image
        }
    }

    result = calls[payload["resource"]][payload["http_method"]](payload)

    return result


def get_image_extension_by_content_type(content_type: str):
    if content_type == 'image/jpeg':
        return 'JPG'
    elif content_type == 'image/png':
        return 'PNG'


def get_images(payload: dict):
    return "None"


def post_image(payload: dict):
    image = {
        "name": payload['headers']['Image-Name'],
        "format": get_image_extension_by_content_type(payload['headers']['Content-Type']),
        "b64_encoded_image": payload['body']
    }

    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['images_s3_bucket_name'])
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['images_dynamodb_information_table'])

    image_to_create = Image(
        bucket, table, image_name=image['name'], image_format=image['format'], encoded_b64_image=image['b64_encoded_image'])

    return image_to_create.save_image()


def get_image(payload: dict):
    # fetch the image information from the DynamoDB table
    s3 = boto3.resource('s3')
    bucket = s3.Bucket(os.environ['images_s3_bucket_name'])
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(os.environ['images_dynamodb_information_table'])

    
    print(payload['path_parameters'])

    image = Image(bucket, table, image_id=payload['path_parameters']['image-id'])

    return image.get_image_http_payload()


def put_image(payload: dict):
    return "None"


def patch_image(payload: dict):
    return "None"


def delete_image(payload: dict):
    return "None"
