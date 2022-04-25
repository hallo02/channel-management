"""
This module fetches the original m3u file, reduces it to streams matching a configured
list of languages and provides this reduced m3u list to s3
"""

import json # pylint: disable=import-error
import shutil # pylint: disable=import-error
import os # pylint: disable=import-error
import urllib3 # pylint: disable=import-error
import boto3 # pylint: disable=import-error

# Secret
SECRET_ARN = os.environ['SECRET_ARN']
REGION_NAME = "eu-west-1"

# S3
BUCKET_NAME = os.environ['S3_BUCKET_NAME']
FILE_NAME = "reduced_channels.m3u"
LANGUAGE_FILTER = ['[DE]','|DE|','[EN]','|EN|','[NL]','|NL|']

# App
TEMP_FILE_IN = "/tmp/origin"
TEMP_FILE_OUT = "/tmp/channeltrimmer-output"


def lambda_handler(_event, _context):
    """ function triggered by cron job """
    server = get_secret("channel.fetcher.server")
    username = get_secret("channel.fetcher.username")
    password = get_secret("channel.fetcher.password")
    url= "http://" + server + ":80/get.php"\
        "?username="  + username +\
        "&password=" + password +\
        "&output=ts&type=m3u_plus"
    download(url, TEMP_FILE_IN)
    process()
    upload()
    return {'statusCode': 200}

def download(url, path):
    """ downloads the origin m3u file """
    http = urllib3.PoolManager()
    with open(path, 'wb') as out:
        response = http.request('GET', url, preload_content=False)
        shutil.copyfileobj(response, out)

def process():
    """ reduces the stream to configured language streams only """
    with open(TEMP_FILE_IN, "r", encoding="utf-8") as file_in:
        with open(TEMP_FILE_OUT, "w", encoding="utf-8") as file_out:
            associated = False
            file_out.write("#EXTM3U\n")
            for line in file_in:
                line = line.strip("\n")
                if associated:
                    file_out.write(line+"\n")
                    associated = False
                    continue
                if any(lng in line for lng in LANGUAGE_FILTER):
                    file_out.write(line+"\n")
                    associated = True

def upload():
    """ uploads the processed m3u file to s3"""
    s3_res = boto3.resource("s3")
    s3_res.meta.client.upload_file(TEMP_FILE_OUT, BUCKET_NAME, FILE_NAME)


def get_secret(key):
    """ obtains secrets to access origin m3u """
    # Create a Secrets Manager client
    session = boto3.session.Session()
    secret_client = session.client(
        service_name='secretsmanager',
        region_name=REGION_NAME
    )
    secrets = secret_client.get_secret_value(SecretId=SECRET_ARN)
    return json.loads(secrets["SecretString"])[key]
