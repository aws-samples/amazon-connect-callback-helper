##CBWitness-ScheduleCall Function
import json
import boto3
import os
import datetime
import pytz
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    print(event)
    CONTACT_TABLE= os.environ['CONTACTS_TABLE']
    
    wakeTime = str(event['Details']['ContactData']['Attributes']['wakeTime'])
    contactId = str(event['Details']['ContactData']['ContactId'])
    contactPhone = str(event['Details']['ContactData']['CustomerEndpoint']['Address'])
    timezone = str(event['Details']['ContactData']['Attributes']['timezone'])
    
    if(wakeTime == "None"):
        wakeTimeFormat = get_time(timezone)
    else:
        wakeTimeFormat = get_custom_time(wakeTime,timezone)
        
    response = add_to_queue(contactPhone, wakeTimeFormat, contactId, CONTACT_TABLE)
    
    return {
        'statusCode': 200,
        'body': json.dumps(response)
    }

    

#===============================

def get_time(time_zone):
    now = datetime.datetime.now(pytz.timezone(time_zone))
    utcNow = now.astimezone(pytz.timezone('UTC'))
    wakeTime = utcNow.replace(second=00,microsecond=00)
    return (wakeTime)

def get_custom_time(time,time_zone):
    timehour=int(time[0:2])
    timemin=(int(time[2:4]) // 10 )* 10
    now = datetime.datetime.now(pytz.timezone(time_zone))
    wakeTime = now.replace(hour=timehour, minute=timemin, second=00,microsecond=00)
    utcWakeTime = wakeTime.astimezone(pytz.timezone('UTC'))
    return (utcWakeTime)

def add_to_queue(phone, wakeTime,contactId, table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)
    
    try:
        response = table.update_item(
            Key={
                'phoneNumber': phone
            }, 
            UpdateExpression='SET #item = :newState, #item2 = :newState2',  
            ExpressionAttributeNames={
                '#item': 'contactId',
                '#item2': 'wakeTime',
            },
            ExpressionAttributeValues={
                ':newState': contactId,
                ':newState2': str(wakeTime),
            },
            ReturnValues="UPDATED_NEW")
        print (response)
    except Exception as e:
        print (e)
    else:
        return response