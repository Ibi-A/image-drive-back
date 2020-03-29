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


class CrudLambdaManager:
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

    def __init__(self, lambda_id, lambda_event, crud_functions: dict):
        self.lambda_id = lambda_id
        self.payload = CrudLambdaManager.__extract_payload(lambda_event)
        self.crud_functions = crud_functions


    def process_call(self):
        """
            Extracts the called HTTP method and resource, invokes the proper
            function and returns the HTTP response.
        """
        response = self.crud_functions[self.payload['context']["resource"]][self.payload['context']["http_method"]](self.payload)

        return response


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



def get_generic_lambda_response(status_code: HTTPStatus, payload: dict):
    response = {
        "statusCode": status_code.value,
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
