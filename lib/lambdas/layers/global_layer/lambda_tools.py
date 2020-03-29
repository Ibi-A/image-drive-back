import json
import boto3
import string
import random

from enum import Enum
from http import HTTPStatus
from typing import final
from abc import ABC, abstractmethod


@final
class HTTPMethod(Enum):
    GET = 'GET'
    POST = 'POST'
    PUT = 'PUT'
    PATCH = 'PATCH'
    DELETE = 'DELETE'


class AWSResourceHelper:
    @staticmethod
    def dynamodb_get_table_item(table, key_name: str, key_value: str) -> dict:
        return table.get_item(Key={key_name: key_value})['Item']


    @staticmethod
    def dynamodb_delete_item(table, key_name: str, key_value: str) -> dict:
        return table.delete_item(Key={key_name: key_value})

    @staticmethod
    def s3_create_presigned_url(bucket_name: str, object_name: str, expiration: int=3600) -> str:
        """
            Generate a presigned URL to share an S3 object

            :param bucket_name: string
            :param object_name: string
            :param expiration: Time in seconds for the presigned URL to remain valid
            :return: Presigned URL as string. If error, returns None.
        """

        # Generate a presigned URL for the S3 object
        s3_client = boto3.client('s3')
        try:
            response = s3_client.generate_presigned_url(
                'get_object',
                Params={'Bucket': bucket_name, 'Key': object_name},
                ExpiresIn=expiration
            )
        except ClientError as e:
            logging.error(e)
            return None

        # The response contains the presigned URL
        return response


    @staticmethod
    def s3_delete_object(bucket, object_name: str) -> dict:
        return bucket.delete_objects(
            Delete={
                'Objects': [
                    {'Key': object_name}
                ]
            }
        )


class GenericTools:
    @staticmethod
    def get_random_id(size: int) -> str:
        random.seed()
        charset = string.digits + string.ascii_letters + '_'

        generated_id = ''

        for _ in range(0, size):
            generated_id = generated_id + \
                charset[random.randint(0, len(charset) - 1)]

        return generated_id


class CRUDInterface(ABC):
    @final
    def __init__(self, collection_path: str, item_path: str):
        self.collection_path = collection_path
        self.item_path = f'{self.collection_path}{item_path}'

    @abstractmethod
    def get_collection(self, payload: dict) -> dict:
        pass

    @abstractmethod
    def post_new_item(self, payload: dict) -> dict:
        pass

    @abstractmethod
    def get_item(self, payload: dict) -> dict:
        pass
    
    @abstractmethod
    def put_item(self, payload: dict) -> dict:
        pass

    @abstractmethod
    def patch_item(self, payload: dict) -> dict:
        pass

    @abstractmethod
    def delete_item(self, payload: dict) -> dict:
        pass

    @final
    def as_dict(self) -> dict:
        return {
            self.collection_path: {
                HTTPMethod.GET: self.get_collection,
                HTTPMethod.POST: self.post_new_item
            },
            self.item_path: {
                HTTPMethod.GET: self.get_item,
                HTTPMethod.PUT: self.put_item,
                HTTPMethod.PATCH: self.patch_item,
                HTTPMethod.DELETE: self.delete_item
            }
        }

@final
class CRUDLambdaManager:
    @classmethod
    def __extract_payload(cls, lambda_event) -> dict:
        payload = {
            'context': {
                'http_method': HTTPMethod(lambda_event['requestContext']['httpMethod']),
                'resource': lambda_event['resource'],
                'path': lambda_event['path'],
                'is_base64_encoded': lambda_event['isBase64Encoded'],
                'request_time': lambda_event['requestContext']['requestTime'],
            },
            'headers': lambda_event['headers'],
            'params': {
                'query_string_params': lambda_event['queryStringParameters'],
                'multi_value_query_string_params': lambda_event['multiValueQueryStringParameters'],
                'path_params': lambda_event['pathParameters'],
            },
            'body': lambda_event['body']  
        }

        return payload


    @staticmethod
    def lambda_http_response(status_code: HTTPStatus, payload: dict) -> dict:
        http_response = {
            'statusCode': status_code.value,
            'headers': {
                'Content-Type': 'application/json'
            },
            'body': json.dumps(payload)
        }

        return http_response


    def __init__(self, lambda_id: str, lambda_event, crud_functions: CRUDInterface):
        self.lambda_id = lambda_id
        self.payload = CRUDLambdaManager.__extract_payload(lambda_event)
        self.crud_functions = crud_functions.as_dict()


    def process_call(self) -> dict:
        """
            Extracts the called HTTP method and resource, invokes the proper
            function and returns the HTTP response.
        """
        http_response = self.crud_functions[self.payload['context']['resource']][self.payload['context']['http_method']](self.payload)

        return http_response
