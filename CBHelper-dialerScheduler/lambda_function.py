##CBWitness-dialerScheduler Function
## Invocation Schema: {'Views': {'ViewResultData': {'CallbackTime': '12:00', 'NotToday': 'true', 'CallbackDate': '2023-07-05', '3PConfirmation': 'true', '3PCallbackPhone': '123123123'}}}
import json
import boto3
import os
from datetime import datetime
import time
import pytz
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    print(event)
    CONTACT_TABLE= os.environ['CONTACTS_TABLE']
    TIME_ZONE= os.environ['TIME_ZONE']

    wakeTime = event['Details']['Parameters']['Views']['ViewResultData']['CallbackTime']
    NotToday =event['Details']['Parameters']['Views']['ViewResultData'].get('NotToday','false')
    CallbackDate = event['Details']['Parameters']['Views']['ViewResultData']['CallbackDate']

    if(event['Details']['Parameters']['Views']['ViewResultData'].get('3PConfirmation','false') == 'true'):
        contactPhone = event['Details']['Parameters']['Views']['ViewResultData']['3PConfirmation']
    else:
        contactPhone = str(event['Details']['ContactData']['CustomerEndpoint']['Address'])
    
    attributes = event['Details']['ContactData']['Attributes']

    wakeTimeFormat = get_custom_time(wakeTime,NotToday,CallbackDate,TIME_ZONE)
        
    response = schedule_callback(contactPhone, wakeTimeFormat, attributes,CONTACT_TABLE)
    
    return {
        'statusCode': 200
    }

def get_custom_time(cb_time,not_today,cb_date,time_zone):
    now = datetime.now(pytz.timezone(time_zone))
    timehour=int(cb_time[0:2])
    timemin=(int(cb_time[3:5]) // 10 )* 10
    if (not_today == 'true'):
        datemonth=int(cb_date[5:7])
        dateday=int(cb_date[8:10])
        wakeTime = now.replace(month=datemonth,day=dateday,hour=timehour, minute=timemin, second=00,microsecond=00)
    else:
        wakeTime = now.replace(hour=timehour, minute=timemin, second=00,microsecond=00)
    utcWakeTime = wakeTime.astimezone(pytz.timezone('UTC'))
    return (utcWakeTime)

def add_to_queue(phone, wakeTime,attributes, table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)
    
    try:
        response = table.update_item(
            Key={
                'phoneNumber': phone
            }, 
            UpdateExpression='SET #item = :newState, #item2 = :newState2',  
            ExpressionAttributeNames={
                '#item': 'attributes',
                '#item2': 'wakeTime',
            },
            ExpressionAttributeValues={
                ':newState': attributes,
                ':newState2': str(wakeTime),
            },
            ReturnValues="UPDATED_NEW")
        print (response)
    except Exception as e:
        print (e)
    else:
        return response

def schedule_callback(phone, wakeTime, attributes,table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)

    timestamp = str(datetime.now())
    timetolive = 7*24*60*60 + int(time.time())
    
    try:
        response = table.update_item(
            Key={
                'phoneNumber': phone
            }, 
            UpdateExpression='SET #item = :newState, #item2 = :newState2, #item3 = :newState3',  
            ExpressionAttributeNames={
                '#item': 'wakeTime',
                '#item2': 'attributes',
                '#item3': 'ttl'
                
            },
            ExpressionAttributeValues={
                ':newState': str(wakeTime),
                ':newState2': attributes,
                ':newState3': timetolive
            },
            ReturnValues="UPDATED_NEW")
        print (response)
    except Exception as e:
        print (e)
    else:
        return response

