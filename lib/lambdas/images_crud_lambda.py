import boto3
import os
import layers.global_layer.lambda_tools as LambdaTools

from base64 import b64decode
from http import HTTPStatus


"""
    Required AWS resources for the CRUD Lambda
"""
s3 = boto3.resource('s3')
bucket = s3.Bucket(os.environ['images_s3_bucket_name'])
dynamodb = boto3.resource('dynamodb')
table = dynamodb.Table(os.environ['images_dynamodb_information_table'])


class Image:
    IMAGE_ID_LENGTH = 16

    @staticmethod
    def get_image_extension_by_content_type(content_type: str) -> str:
        if content_type == 'image/jpeg':
            return 'JPG'
        elif content_type == 'image/png':
            return 'PNG'

    def __init__(self, s3_bucket, dynamodb_table, image_id: str=None, image_name: str=None, image_format: str=None, b64_encoded_image=None):
        self.s3_bucket = s3_bucket
        self.dynamodb_table = dynamodb_table

        # if the image already exists in the drive, load it
        if image_id is not None:
            self.image_id = image_id

            image_info = LambdaTools.AWSResourceHelper.dynamodb_get_table_item(
                self.dynamodb_table, 'id', self.image_id)

            self.image_name = image_info['name']
            self.image_format = image_info['format']
            self.image_s3_key = image_info['s3_key']

        # if the image does not exist, create an ID and initialize it
        elif (image_name and image_format and b64_encoded_image) is not None:
            self.image_id = LambdaTools.GenericTools.get_random_id(Image.IMAGE_ID_LENGTH)
            self.image_name = image_name
            self.image_format = image_format.upper()
            self.image_s3_key = f'{self.image_id}.{self.image_format.lower()}'
            self.b64_encoded_image = b64_encoded_image

    def get_image(self) -> dict:
        redirect_url = LambdaTools.AWSResourceHelper.s3_create_presigned_url(
            self.s3_bucket.name, self.image_s3_key)

        payload = self.as_dict(redirect_url)
        
        return payload

    def save_image(self) -> dict:
        decoded_image = b64decode(self.b64_encoded_image)

        self.s3_bucket.put_object(
            Key=f"{self.image_s3_key}", Body=decoded_image, ACL='public-read')

        self.dynamodb_table.put_item(
            Item={
                'id': self.image_id,
                'name': self.image_name,
                'format': self.image_format,
                's3_key': self.image_s3_key
            }
        )

        redirect_url = LambdaTools.AWSResourceHelper.s3_create_presigned_url(
            self.s3_bucket.name, self.image_s3_key)
        payload = self.as_dict(redirect_url)

        return payload

    def delete_image(self) -> None:
        LambdaTools.AWSResourceHelper.s3_delete_object(self.s3_bucket, self.image_s3_key)
        LambdaTools.AWSResourceHelper.dynamodb_delete_item(self.dynamodb_table, 'id', self.image_id)

        return None

    def as_dict(self, s3_presigned_url: str) -> dict:
        return {
            'id': self.image_id,
            'name': self.image_name,
            'format': self.image_format,
            'uri': s3_presigned_url
        }


class CRUDImage(LambdaTools.CRUDInterface):
    def get_collection(self, payload: dict) -> dict:
        """
            Function reponsible for GET /images
        """
        return "None"


    def post_new_item(self, payload: dict) -> dict:
        """
            Function reponsible for POST /images
        """
        image_payload = {
            'name': payload['headers']['Image-Name'],
            'format': Image.get_image_extension_by_content_type(payload['headers']['Content-Type']),
            'b64_encoded_image': payload['body']
        }

        image = Image(
            bucket, table,
            image_name=image_payload['name'],
            image_format=image_payload['format'],
            b64_encoded_image=image_payload['b64_encoded_image']
        )

        return LambdaTools.CRUDLambdaManager.lambda_http_response(
            HTTPStatus.CREATED,
            image.save_image()
        )


    def get_item(self, payload: dict) -> dict:
        """
            Function reponsible for GET /images/{image-id}
        """
        image = Image(
            bucket, table,
            image_id=payload['params']['path_params']['image-id']
        )

        return LambdaTools.CRUDLambdaManager.lambda_http_response(
            HTTPStatus.OK,
            image.get_image()
        )


    def put_item(self, payload: dict) -> dict:
        """
            Function reponsible for PUT /images/{image-id}
        """
        return "None"


    def patch_item(self, payload: dict) -> dict:
        """
            Function reponsible for PATCH /images/{image-id}
        """
        return "None"


    def delete_item(self, payload: dict) -> dict:
        """
            Function reponsible for DELETE /images/{image-id}
        """
        image = Image(
            bucket, table,
            image_id=payload['params']['path_params']['image-id']
        )

        return LambdaTools.CRUDLambdaManager.lambda_http_response(
            HTTPStatus.NO_CONTENT,
            image.delete_image()
        )


def lambda_handler(event, _):
    """
        Lambda responsible for processing CRUD operations on images.

        Extracts the payload received from the API call and processes it
        accordingly.
    """
    crud_lambda_manager = LambdaTools.CRUDLambdaManager(
        'images_crud_lambda', event,
        CRUDImage('/images', '/{image-id}')
    )

    return crud_lambda_manager.process_call()

