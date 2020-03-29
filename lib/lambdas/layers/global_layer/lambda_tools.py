import json
import boto3
import string
import random

from enum import Enum
from http import HTTPStatus


class HTTPMethod(Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"


class AWSResourceHelper:
    @staticmethod
    def dynamodb_get_table_item(dynamodb_table, key_name, key_value):
        return dynamodb_table.get_item(
            Key={
                key_name: key_value
            }
        )['Item']


    @staticmethod
    def s3_create_presigned_url(bucket_name, object_name, expiration=3600):
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


    @staticmethod
    def s3_delete_object(bucket, object_name):
        return bucket.delete_objects(
            Delete={
                'Objects': [
                    {
                        'Key': object_name
                    }
                ]
            }
        )

    @staticmethod
    def dynamodb_delete_item(table, key_name, key_value):
        return table.delete_item(
            Key={
                key_name: key_value
            }
        )


class GenericTools:
    @staticmethod
    def get_random_id(size: int):
        random.seed()
        charset = string.digits + string.ascii_letters + '_'

        generated_id = ""

        for _ in range(0, size):
            generated_id = generated_id + \
                charset[random.randint(0, len(charset) - 1)]

        return generated_id


class CRUDInterface():
    def __init__(self, collection_path: str, item_path: str):
        self.collection_path = collection_path
        self.item_path = f'{self.collection_path}{item_path}'


    def get_collection(self, payload: dict):
        pass

    def post_new_item(self, payload: dict):
        pass

    def get_item(self, payload: dict):
        pass

    def put_item(self, payload: dict):
        pass

    def patch_item(self, payload: dict):
        pass

    def delete_item(self, payload: dict):
        pass

    
    def as_dict(self):
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


class CRUDLambdaManager:
    @classmethod
    def __extract_payload(cls, lambda_event):
        payload = {
            "context": {
                "http_method": HTTPMethod(lambda_event['requestContext']['httpMethod']),
                "resource": lambda_event['resource'],
                "path": lambda_event['path'],
                "is_base64_encoded": lambda_event['isBase64Encoded'],
                "request_time": lambda_event['requestContext']['requestTime'],
            },
            "headers": lambda_event['headers'],
            "params": {
                "query_string_params": lambda_event['queryStringParameters'],
                "multi_value_query_string_params": lambda_event['multiValueQueryStringParameters'],
                "path_params": lambda_event['pathParameters'],
            },
            "body": lambda_event['body']  
        }

        return payload


    @staticmethod
    def lambda_http_response(status_code: HTTPStatus, body: dict):
        response = {
            "statusCode": status_code.value,
            "headers": {
                'Content-Type': 'application/json'
            },
            "body": json.dumps(body)
        }

        return response


    def __init__(self, lambda_id, lambda_event, crud_functions: CRUDInterface):
        self.lambda_id = lambda_id
        self.payload = CRUDLambdaManager.__extract_payload(lambda_event)
        self.crud_functions = crud_functions.as_dict()


    def process_call(self):
        """
            Extracts the called HTTP method and resource, invokes the proper
            function and returns the HTTP response.
        """
        response = self.crud_functions[self.payload['context']["resource"]][self.payload['context']["http_method"]](self.payload)

        return response
