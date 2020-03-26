import json
import boto3


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