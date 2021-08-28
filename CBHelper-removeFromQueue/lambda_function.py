##CBWitness-Remove from Queue Function
import json
import boto3
import os
import datetime
from boto3.dynamodb.conditions import Key

def lambda_handler(event, context):
    print(event)
    CONTACTS_TABLE= os.environ['CONTACTS_TABLE']
    
    contactId = str(event['Details']['ContactData']['ContactId'])
    contactPhone = str(event['Details']['ContactData']['CustomerEndpoint']['Address'])
    
    response = remove_contactId(contactPhone,CONTACTS_TABLE)
    
    return response
    

#===============================

def remove_contactId(phone,table):
    dynamodb = boto3.resource('dynamodb')
    table = dynamodb.Table(table)

    try:
        response = table.delete_item(
            Key={
                'phoneNumber': phone
            }
        )
    except Exception as e:
        print (e)
    else:
        return response
