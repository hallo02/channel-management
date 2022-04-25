"""
This module delivers the preprocessed reduced channel m3u file
"""

import json # pylint: disable=import-error
import boto3 # pylint: disable=import-error
import os # pylint: disable=import-error

# Secret
SECRET_ARN = os.environ['SECRET_ARN']
SECRET_KEY = "channel.provider.request-password"
SECRET_REGION_NAME = "eu-west-1"

# S3 Bucket
S3_BUCKET_NAME = os.environ['S3_BUCKET_NAME']
S3_FILE_NAME = "reduced_channels.m3u"


def lambda_handler(event, _context):
    """ This function is triggered by an endpoint GET request """
    request_password = event["queryStringParameters"]["password"]
    if request_password != get_request_password():
        return  {'statusCode': 401}
    response = get_presigned_url()
    return {
        'statusCode': 302,
         'headers': {
            'Location': response,
            'Cache-Controle': 'no-cache, no-store, must-revalidate',
            'Pragma': 'no-cache',
            'Expires': 0
        }
    }

def get_presigned_url():
    """ Produces the presigned s3 url to the reduced m3u playlist """
    s3_client = boto3.client('s3')
    return s3_client.generate_presigned_url(
        'get_object',
        Params={'Bucket': S3_BUCKET_NAME,'Key': S3_FILE_NAME},
        ExpiresIn=3600
    )

def get_request_password():
    """ Returns the configured request password from aws secret manager """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    secret_client = session.client(
        service_name='secretsmanager',
        region_name=SECRET_REGION_NAME
    )
    secrets = secret_client.get_secret_value(SecretId=SECRET_ARN)
    return json.loads(secrets["SecretString"])[SECRET_KEY]
