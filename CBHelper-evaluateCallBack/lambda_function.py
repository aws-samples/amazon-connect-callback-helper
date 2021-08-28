##CBWitness-EvaluateCallBack Function
import json
import boto3
import os
import datetime
import pytz
import base64
from botocore.exceptions import ClientError
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    print(event)

    CONTACTS_TABLE= os.environ['CONTACTS_TABLE']
    contactPhone = str(event['Details']['ContactData']['CustomerEndpoint']['Address'])
    
    CONFIG_SECRET= os.environ['CONFIG_SECRET']
    connect_config=json.loads(get_config(CONFIG_SECRET))
    
    instanceId = connect_config['CONNECT_INSTANCE_ID']
    queueId =connect_config['CONNECT_QUEUE_ID']

    timezone = str(event['Details']['ContactData']['Attributes']['timezone'])
    
    if('minimumperiod' in event['Details']['ContactData']['Attributes']): MinTimeWindow = int(event['Details']['ContactData']['Attributes']['minimumperiod'])
    else: MinTimeWindow = 60
    
    if('maximumcbcontacts' in event['Details']['ContactData']['Attributes']): MaxContacts = int(event['Details']['ContactData']['Attributes']['maximumcbcontacts'])
    else: MaxContacts = 10

    if('slopedperiod' in event['Details']['ContactData']['Attributes']): slopedPeriod = int(event['Details']['ContactData']['Attributes']['slopedperiod'])
    else: slopedPeriod = True
    
    print("MaxContacts:" + str(MaxContacts))
    print("MinTimeWindow:" + str(MinTimeWindow))
    print("MinTimeWindow:" + str(slopedPeriod))

    queuedContacts=get_queued_contacts(instanceId,queueId)
    
    print("Contacts in Queue:" + str(queuedContacts))
    
    if(phone_lookup(contactPhone, CONTACTS_TABLE)):
        alreadyQueued=True
    else:
        alreadyQueued=False
    
    closing_time=get_closing_time(instanceId, queueId)

    if(not(alreadyQueued) and queuedContacts <= MaxContacts):
        response ={"cbTier" : get_allowed_tier(MinTimeWindow,closing_time['Hours'],closing_time['Minutes'],timezone, slopedPeriod )}
    else:
        response ={"cbTier" : "notvalid"}
    return response
    

#===============================

def get_allowed_tier(MinTimeWindow,EndTimeHours,EndTimeMins, time_zone, slopedPeriod):
    
    now = datetime.datetime.now(pytz.timezone(time_zone))
    utcNow=now.astimezone(pytz.timezone('UTC'))
    closingTime = utcNow.replace(hour=EndTimeHours, minute=EndTimeMins,second=00)
    
    availTime = closingTime-now
    availMins = availTime.seconds/60
    if (slopedPeriod and availMins >= 0):
        availRatio = availMins / MinTimeWindow
        if (availRatio == 0): availTier = "notvalid"
        if (availRatio < .25): availTier = "below25"
        if (availRatio < .5 and availRatio >=.25): availTier = "below50" 
        if (availRatio < .75 and availRatio >=.5): availTier = "below75" 
        if (availRatio >=.75 and availRatio <1): availTier = "below100" 
        if (availRatio >= 1): availTier = "valid" 
    elif (availMins >= 0): availTier = "valid"
    else: availTier = "notvalid"

    return (availTier)
    
def get_queued_contacts(instanceId,queueId):
    connect = boto3.client('connect')
    response = connect.get_current_metric_data(
        InstanceId=instanceId,
        Filters={
            'Queues': [
                queueId,
            ],
            'Channels': [
                'VOICE',
            ]
        },
        Groupings=[
            'QUEUE',
        ],
        CurrentMetrics=[
            {
                'Name': 'CONTACTS_IN_QUEUE',
                'Unit': 'COUNT'
            },
        ]
    )
    print(response['MetricResults'])
    return int(response['MetricResults'][0]['Collections'][0]['Value'])


def get_closing_time(instanceId, queueId):

    connect = boto3.client('connect')
    
    queue = connect.describe_queue(
        InstanceId=instanceId,
        QueueId=queueId
        )
        
    hours = connect.describe_hours_of_operation(
        InstanceId=instanceId,
        HoursOfOperationId=queue['Queue']['HoursOfOperationId']
        )
    now = datetime.datetime.now()
    today=now.strftime("%A")
    closingTime = list(filter(lambda x:x["Day"]==today.upper(),hours['HoursOfOperation']['Config']))
    
    return closingTime[0]['EndTime']



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

def remove_contactId(phone,table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)

    try:
        response = table.delete_item(
            Key={
                'contactId': phone
            }
        )
    except Exception as e:
        print (e)
    else:
        return response


def phone_lookup(phone, table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)
    response = table.query(
        KeyConditionExpression=Key('phoneNumber').eq(phone)
    )
    if (response['Count']): 
        print("Found contact:" + str(response['Items'][0]))
        contactId = response['Items'][0]['contactId']
    else:
        print("Not contact found")
        contactId = False
    return contactId

def update_contact(phone, contactId, table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)
    
    try:
        response = table.update_item(
            Key={
                'phone': phone
            }, 
            UpdateExpression='SET #item = :newState',  
            ExpressionAttributeNames={
                '#item': 'contactId'
            },
            ExpressionAttributeValues={
                ':newState': contactId
            },
            ReturnValues="UPDATED_NEW")
        print (response)
    except Exception as e:
        print (e)
    else:
        return response