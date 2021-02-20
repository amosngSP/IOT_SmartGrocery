#!/usr/bin/python
import sys
import requests
import json
import boto3
from botocore.exceptions import ClientError 
api_key = "3C84072AE757BA0B54F8FDA0BF44A64F" #https://upcdatabase.org/

class Dynamodb():
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
    def get(self,tablename,key):
        try:
            table = self.dynamodb.Table(tablename)
            response = table.get_item(Key=key)
            if len(response)>0:
                if "Item" in response:
                    return response['Item']
                else:
                    return False
            else:
                return False
        except ClientError as e:
            print("ClientError occurred!")
            print(e)
            print("tablename:{} provided key:{}".format(tablename,key))
            return False
    def add(self,tablename,values):
        try:
            table = self.dynamodb.Table(tablename)
            table.put_item(Item=values)
            return True
        except ClientError:
            print("Error! ValidationException occurred, could not add to DynamoDB!")
            return False
    def update(self,tablename,key,upd_expression,values=None):
        try:
            table = self.dynamodb.Table(tablename)
            if values is None:
                resp = table.update_item(Key=key,UpdateExpression=upd_expression)
            else:
                resp = table.update_item(Key=key,UpdateExpression=upd_expression,ExpressionAttributeValues=values)
            return resp
        except ClientError as e:
            print("Error! ValidationException occurred, could not update DynamoDB!")
            print(e)
            return False
dynamodb = Dynamodb()

def add_deduct_item(upc,mode):
    #check if inventory item exists:
    key = {'upc':upc}
    response = dynamodb.get("inventory",key)
    if response:
        #in database

        #check mode
        if mode == 0:
            #deduct mode
            upd_expression = "SET qty = qty - :val"
        else:
            #add mode
            upd_expression = "SET qty = qty + :val"
        
        key = {'upc':upc}
        values = {':val':1}
        response = dynamodb.update("inventory",key,upd_expression,values)
        return response
    else:
        #not in database
        #create entry
        #Note to self:This part should always be an add, no deduct.
        #Function should only trigger if add_if_not_exist_item is true.
        values = {"upc":upc,"qty":1}
        response = dynamodb.add("inventory",values)
        return response
        

def add_if_not_exist_item(upc):
    key = {'upc':upc}
    response = dynamodb.get("upc_product",key)
    if response:
        #in database
        return True
    else:
        #find in the UPC Database
        lookup = UPC_lookup(upc)
        if lookup:
            #Found
            item_desc = "Unknown"
            if lookup['title'].strip() != "":
                print(len(lookup['title'].strip()))
                print(lookup['title'])
                item_desc = lookup['title']
            elif lookup['description'].strip() != "":
                item_desc = lookup['description']
            values = {"upc":upc,"item_desc":item_desc,"threshold":0}
            dynamodb.add("upc_product",values)
            values = {"upc":upc,"qty":0}
            dynamodb.add("inventory",values)
            return True
        else:
            return False

def barcode_reader():
    """Barcode code obtained from 'brechmos' 
    https://www.raspberrypi.org/forums/viewtopic.php?f=45&t=55100"""
    hid = {4: 'a', 5: 'b', 6: 'c', 7: 'd', 8: 'e', 9: 'f', 10: 'g', 11: 'h', 12: 'i', 13: 'j', 14: 'k', 15: 'l', 16: 'm',
           17: 'n', 18: 'o', 19: 'p', 20: 'q', 21: 'r', 22: 's', 23: 't', 24: 'u', 25: 'v', 26: 'w', 27: 'x', 28: 'y',
           29: 'z', 30: '1', 31: '2', 32: '3', 33: '4', 34: '5', 35: '6', 36: '7', 37: '8', 38: '9', 39: '0', 44: ' ',
           45: '-', 46: '=', 47: '[', 48: ']', 49: '\\', 51: ';', 52: '\'', 53: '~', 54: ',', 55: '.', 56: '/'}

    hid2 = {4: 'A', 5: 'B', 6: 'C', 7: 'D', 8: 'E', 9: 'F', 10: 'G', 11: 'H', 12: 'I', 13: 'J', 14: 'K', 15: 'L', 16: 'M',
            17: 'N', 18: 'O', 19: 'P', 20: 'Q', 21: 'R', 22: 'S', 23: 'T', 24: 'U', 25: 'V', 26: 'W', 27: 'X', 28: 'Y',
            29: 'Z', 30: '!', 31: '@', 32: '#', 33: '$', 34: '%', 35: '^', 36: '&', 37: '*', 38: '(', 39: ')', 44: ' ',
            45: '_', 46: '+', 47: '{', 48: '}', 49: '|', 51: ':', 52: '"', 53: '~', 54: '<', 55: '>', 56: '?'}

    fp = open('/dev/hidraw1', 'rb')

    ss = ""
    shift = False

    done = False

    while not done:

        ## Get the character from the HID
        buffer = fp.read(8)
        for c in buffer:
            if int(c) > 0:

                ##  40 is carriage return which signifies
                ##  we are done looking for characters
                if int(c) == 40:
                    done = True
                    break;

                ##  If we are shifted then we have to
                ##  use the hid2 characters.
                if shift:

                    ## If it is a '2' then it is the shift key
                    if int(c) == 2:
                        shift = True

                    ## if not a 2 then lookup the mapping
                    else:
                        ss += hid2[int(c)]
                        shift = False

                ##  If we are not shifted then use
                ##  the hid characters

                else:

                    ## If it is a '2' then it is the shift key
                    if int(c) == 2:
                        shift = True

                    ## if not a 2 then lookup the mapping
                    else:
                        ss += hid[int(c)]
    return ss

def UPC_lookup(upc):
    '''V3 API'''

    url = "https://api.upcdatabase.org/product/%s?apikey=%s" % (upc, api_key)

    headers = {
        'cache-control': "no-cache",
    }

    response = requests.request("GET", url, headers=headers)
    if response.status_code == 200:
        resp = response.json()
        print(resp)
        if resp['success']:
            return resp
        else:
            return False
    else:
        return False
    #print("-----" * 5)
    #print(upc)
    #print(json.dumps(response.json(), indent=2))
    #print("-----" * 5 + "\n")
