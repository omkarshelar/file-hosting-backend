from chalice import Chalice, CORSConfig
import boto3
import uuid
from chalicelib import utils
from secrets import token_urlsafe
import time

app = Chalice(app_name='file-hosting-apis')

cors_config = CORSConfig(
    allow_origin='*',
    allow_headers=['Content-Type', 'Authorization',
                   'X-Amz-Date', 'X-Api-Key', 'X-Amz-Security-Token'],
    max_age=600,
    allow_credentials=True
)


S3 = boto3.client('s3')
DYNAMODB = boto3.client('dynamodb')

BUCKET_NAME = 'file-hosting-app'
TABLE_NAME = 'file-hosting-app'

@app.route('/signed-url-upload/{key}', methods=['GET'], cors=cors_config)
def upload_url(key):
    key = token_urlsafe(32) + key
    url = S3.generate_presigned_url('put_object', Params={'Bucket':BUCKET_NAME,'Key':key}, ExpiresIn=300, HttpMethod='PUT')

    return {
        "UploadURL": url,
        "Key": key
    }

@app.route('/custom-uri/{key}/{ttl}', methods=['POST'], cors=cors_config)
def get_custom_uri(key, ttl):
    random_uri = str(uuid.uuid4())
    response = DYNAMODB.put_item(TableName=TABLE_NAME,
    Item={
        "RANDOM_URI": {
            "S": random_uri
        },
        "KEY": {
            "S": key
        },
        "EXPIRES": {
            "N": ttl
        }
    })

    if(response["ResponseMetadata"]["HTTPStatusCode"] == 200):
        return utils.make_response(201, {
            "URL": random_uri
        })
    else:
        res = S3.delete_object(Bucket=BUCKET_NAME, Key=key)
        if(response["ResponseMetadata"]["HTTPStatusCode"] == 204):
            return utils.make_response(500, {
                "message": "Sorry an error occured. Please try again later.",
                "object_delete": True
            })
        else:
            return utils.make_response(500, {
                "message": "Sorry an error occured. Please try again later.",
                "object_delete": False
            })

@app.route('/asset/{custom_id}', methods=['GET'], cors=cors_config)
def get_asset(custom_id):
    try:
        response = DYNAMODB.query(TableName=TABLE_NAME,
        KeyConditionExpression = "RANDOM_URI = :id",
        FilterExpression="EXPIRES >= :current_time",
        ExpressionAttributeValues = {
            ":id": {
                "S": custom_id
            },
            ":current_time": {
                "N": str(int(time.time()))
            }
        })
        print(response)
    except Exception as e:
        print(e)
        return utils.make_response(500, {
            "message": "Something went wrong on our end. Please try again in some time."
        })

    if(response["ResponseMetadata"]["HTTPStatusCode"] == 200 and response["Count"] > 0):
        url = utils.download_url(response["Items"][0]["KEY"]["S"])
        res = utils.make_response(307, {}, {
            "Location": url
        })
    else:
        with open('chalicelib/404.html', 'r') as f:
            error_page = f.read()
            res = utils.make_response(404, error_page,{
                'Content-Type': 'text/html'
            })

    return res
