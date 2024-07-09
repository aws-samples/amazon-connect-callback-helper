##queue Scheduled Callbacks

import json
import boto3
import os
import datetime
import pytz
from boto3.dynamodb.conditions import Key

PRIORITY_SQS_URL = os.environ['PRIORITY_SQS_URL']

def lambda_handler(event, context):

    CONTACTS_TABLE= os.environ['CONTACTS_TABLE']
    WAKE_INDEX = 'wakeTime'
    TIME_ZONE='UTC'
    
    wakeTime=get_time(TIME_ZONE)
    contacts = get_contacts(str(wakeTime), CONTACTS_TABLE, WAKE_INDEX)
    for contact in contacts:
        print ("Encolando contacto: " + contact['phoneNumber'])
        queue_contact(contact['attributes']['custID'],contact['phoneNumber'],contact['attributes'],PRIORITY_SQS_URL)
        
    return True

def get_time(time_zone):
    now = datetime.datetime.now(pytz.timezone(time_zone))
    wakeTime = now.replace(second=00,microsecond=00)
    return (wakeTime)

def get_contacts(time, table, index):
    dynamodb = boto3.resource('dynamodb')
    
    table = dynamodb.Table(table)
    response = table.query(
        IndexName=index,
        KeyConditionExpression=Key('wakeTime').eq(time)
    )
    return response['Items']

def start_machine(phoneNumber,machine):
    client = boto3.client('stepfunctions')
    response = client.start_execution(
        stateMachineArn=machine,
        input="{\"contacts\":{\"phoneNumber\":\"" + phoneNumber + "\"}}"
    )

def queue_contact(custID,phone,attributes,sqs_url):
    sqs = boto3.client('sqs')
    try:
        response = sqs.send_message(
            QueueUrl=sqs_url,
            MessageAttributes={
                'custID': {
                    'DataType': 'String',
                    'StringValue': custID
                },
                'phone': {
                    'DataType': 'String',
                    'StringValue': phone
                },
                'attributes': {
                    'DataType': 'String',
                    'StringValue': json.dumps(attributes)
                }
            },
            MessageBody=(
                phone
            )
        )
    except ClientError as e:
        print(e.response['Error'])
        return False
    else:
        return response['MessageId']

    
def place_call(phoneNumber, contactFlow,connectID,queue):
    connect_client = boto3.client('connect')
    try:
        response = connect_client.start_outbound_voice_contact(
            DestinationPhoneNumber=phoneNumber,
            ContactFlowId=contactFlow,
            InstanceId=connectID,
            QueueId=queue,
            )
    except Exception as e:
        print(e)
        print("phone" + str(phoneNumber))
        response = None
    return response

def remove_contactId(phoneNumber,table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)

    try:
        response = table.delete_item(
            Key={
                'phoneNumber': phoneNumber
            }
        )
    except Exception as e:
        print (e)
    else:
        return response

def queue_contact(custID,phone,attributes,sqs_url):
    sqs = boto3.client('sqs')
    try:
        response = sqs.send_message(
            QueueUrl=sqs_url,
            MessageAttributes={
                'custID': {
                    'DataType': 'String',
                    'StringValue': custID
                },
                'phone': {
                    'DataType': 'String',
                    'StringValue': phone
                },
                'attributes': {
                    'DataType': 'String',
                    'StringValue': json.dumps(attributes)
                }
            },
            MessageBody=(
                phone
            )
        )
    except ClientError as e:
        print(e.response['Error'])
        return False
    else:
        return response['MessageId']

