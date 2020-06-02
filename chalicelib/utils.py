from chalice import Response
import boto3

S3 = boto3.client('s3')
BUCKET_NAME = 'file-hosting-app'

default_headers = {
}

def make_response(status_code, body, headers={}):
    response_headers = dict()
    response_headers.update(default_headers)
    response_headers.update(headers)
    return Response(
        status_code=status_code,
        headers=response_headers,
        body=body)


def download_url(key):
    url = S3.generate_presigned_url('get_object', Params={'Bucket':BUCKET_NAME,'Key':key}, ExpiresIn=300, HttpMethod='GET')

    return url