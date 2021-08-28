##CBWitness-Notify Function
import os
import json
import boto3
import base64
from botocore.exceptions import ClientError

def lambda_handler(event, context):
    CONFIG_SECRET= os.environ['CONFIG_SECRET']
    connect_config=json.loads(get_config(CONFIG_SECRET))
    
    region = connect_config['PP_REGION']
    originationNumber =connect_config['PP_ORIGINATING_NUMBER']
    applicationId=connect_config['PP_PROJECT_ID']
    wakeTime = str(event['Details']['ContactData']['Attributes']['wakeTime'])
    contactPhone = str(event['Details']['ContactData']['CustomerEndpoint']['Address'])
    message = ("We will call back by: " + wakeTime + " at:" + contactPhone)
    
    response = sendNotification(message, originationNumber,contactPhone,applicationId,region)
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }

    
    
def sendNotification(message, originationNumber,destinationNumber,applicationId,region):

    messageType = "TRANSACTIONAL"
    client = boto3.client('pinpoint',region_name=region)
    try:
        response = client.send_messages(
            ApplicationId=applicationId,
            MessageRequest={
                'Addresses': {
                    destinationNumber: {
                        'ChannelType': 'SMS'
                    }
                },
                'MessageConfiguration': {
                    'SMSMessage': {
                        'Body': message,
                        'MessageType': messageType,
                        'OriginationNumber': originationNumber
                    }
                }
            }
        )
    
    except ClientError as e:
        print(e.response['Error']['Message'])
        return None
    else:
        print("Message sent! Message ID: "
                + response['MessageResponse']['Result'][destinationNumber]['MessageId'])
        return response

def get_config(secret_name):
    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager'
    )

    # In this sample we only handle the specific exceptions for the 'GetSecretValue' API.
    # See https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
    # We rethrow the exception by default.

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        if e.response['Error']['Code'] == 'DecryptionFailureException':
            # Secrets Manager can't decrypt the protected secret text using the provided KMS key.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InternalServiceErrorException':
            # An error occurred on the server side.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidParameterException':
            # You provided an invalid value for a parameter.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'InvalidRequestException':
            # You provided a parameter value that is not valid for the current state of the resource.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
        elif e.response['Error']['Code'] == 'ResourceNotFoundException':
            # We can't find the resource that you asked for.
            # Deal with the exception here, and/or rethrow at your discretion.
            raise e
    else:
        # Decrypts secret using the associated KMS CMK.
        # Depending on whether the secret is a string or binary, one of these fields will be populated.
        if 'SecretString' in get_secret_value_response:
            secret = get_secret_value_response['SecretString']
        else:
            decoded_binary_secret = base64.b64decode(get_secret_value_response['SecretBinary'])
    return secret