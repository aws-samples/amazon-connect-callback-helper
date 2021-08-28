##startScheduledCalls Function
import json
import boto3
import os
import datetime
import pytz
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):

    CONTACTS_TABLE= os.environ['CONTACTS_TABLE']
    MACHINE_ID= os.environ['MACHINE_ID']
    WAKE_INDEX = 'wakeTime'
    TIME_ZONE='UTC'
    
    wakeTime=get_time(TIME_ZONE)
    contacts = get_contacts(str(wakeTime), CONTACTS_TABLE, WAKE_INDEX)
    for contact in contacts:
        print ("Iniciando contacto: " + contact['phoneNumber'])
        start_machine(contact['phoneNumber'], MACHINE_ID)
        
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