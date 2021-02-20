# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

import boto3
from boto3.dynamodb.conditions import Key
from botocore.exceptions import ClientError
from django.contrib.auth import authenticate, login
from django.http import JsonResponse, HttpResponse
# Create your views here.
from django.shortcuts import render, redirect
import simplejson
from django.views.decorators.csrf import csrf_exempt
from datetime import datetime
from .forms import LoginForm, SignUpForm

# Credits for the BotHandler Class
# https://github.com/magnitopic/YouTubeCode

import requests


class BotHandler:
    token = '1620569172:AAEoFuZf02nunzAHPrUhyt50lGexusDrFIE'  # Telegram Bot Token

    def __init__(self):
        self.api_url = "https://api.telegram.org/bot{}/".format(self.token)

    # url = "https://api.telegram.org/bot<token>/"

    def get_updates(self, offset=0, timeout=30):
        method = 'getUpdates'
        params = {'timeout': timeout, 'offset': offset}
        resp = requests.get(self.api_url + method, params)
        result_json = resp.json()['result']
        return result_json

    def send_message(self, chat_id, text):
        params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
        method = 'sendMessage'
        resp = requests.post(self.api_url + method, params)
        return resp

    def send_messages(self, chat_id, text):
        for x in chat_id:
            params = {'chat_id': x, 'text': text, 'parse_mode': 'HTML'}
            method = 'sendMessage'
            resp = requests.post(self.api_url + method, params)
        return True

    def get_first_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[0]
        else:
            last_update = None

        return last_update


class Dynamodb():
    def __init__(self):
        self.dynamodb = boto3.resource('dynamodb')
    def get_all(self, tablename):
        table = self.dynamodb.Table(tablename)
        response = table.scan()
        if 'Items' in response:
            return table.scan()['Items']
        else:
            return False
    def get_all_filter(self,tablename,device_name):
        table = self.dynamodb.Table(tablename)
        startdate = "2021-02"
        response = table.query(
            KeyConditionExpression=Key('deviceid').eq(device_name) & Key('datetimeid').begins_with(startdate),
            ScanIndexForward=False
        )
        items = response['Items']
        data = items[:10]
        return data[::-1]
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
    def delete(self,tablename,key):
        try:
            table = self.dynamodb.Table(tablename)
            resp = table.delete_item(Key=key)
            return resp
        except ClientError as e:
            print("Error! ValidationException occurred, could not update DynamoDB!")
            print(e)
            return False
dynamodb = Dynamodb()
IOTbot = BotHandler()
@csrf_exempt
def check_upc(request):
    #check on the upc
    print(request.POST['upc'])
    upc = int(request.POST['upc'])
    #fetch inventory
    inventory = dynamodb.get("inventory", {"upc": upc})
    #get qty
    qty = inventory['qty']
    #fetch upc_product
    upc_product = dynamodb.get("upc_product", {"upc": upc})
    item_desc = upc_product['item_desc']
    threshold = upc_product['threshold']
    if qty <= threshold:
        #fetch subscriber list
        subscribers = dynamodb.get_all("subscribe")
        if subscribers:
            for x in subscribers:
                if x['s_status'] == 1:
                    #subscriber
                    chat_id = x['chat_id']
                    message = "The following product is low on quantity, please refill! Item Description: {} Quantity Left: {}".format(item_desc,qty)
                    IOTbot.send_message(chat_id,message)
    return JsonResponse(True,safe=False)



def get_grocery_list(request):
    #fetch from inventory
    #compare with threshold value in upc_product
    inventory = dynamodb.get_all("inventory")
    list = []
    for x in inventory:
        #fetch the threshold value
        upc = x['upc']
        qty = int(x['qty'])
        upc_product = dynamodb.get("upc_product", {"upc": upc})
        threshold_value = int(upc_product['threshold'])
        item_desc = upc_product['item_desc']
        if qty <= threshold_value:
            item = {"item_desc":item_desc,"qty":qty}
            list.append(item)
    json = {"data":list}
    return JsonResponse(json,safe=False)

def get_barcode_status(request):
    #False - Deduct Mode
    #True - Add Mode
    Key = {'id': 1}
    result = dynamodb.get('barcode_status', Key)
    if result:
        mode = result['b_mode']
        if mode == 0:
            return JsonResponse("0", safe=False)
        else:
            return JsonResponse("1", safe=False)
    else:
        return JsonResponse("-1", safe=False)

def toggle_barcode_status(request):
    Key = {'id': 1}
    result = dynamodb.get('barcode_status', Key)
    if result:
        mode = result['b_mode']
        if mode == 0:
            mode = 1
        else:
            mode = 0
        print(mode)
        ExpressionAttributeValues = {':val1': mode}
        Key = {'id': 1}
        UpdateExpression = 'SET b_mode = :val1'
        resp = dynamodb.update('barcode_status', Key, UpdateExpression, ExpressionAttributeValues)
        if resp:
            return JsonResponse(True, safe=False)
        else:
            return JsonResponse(False, safe=False)

def live_graph(request):
    results = dynamodb.get_all_filter("device_values", "deviceid_light")
    labels = []
    data = []
    for x in results:
        y = int(x["value"])
        if y > 600:
            y = 1
        else:
            y = 0
        z = x['datetimeid']
        z = z.split(".")[0]
        z = datetime.strptime(z, "%Y-%m-%dT%H:%M:%S")
        time = "{}:{}:{}".format(str(z.hour).zfill(2), str(z.minute).zfill(2), str(z.second).zfill(2))
        labels.append(time)
        data.append(y)
        # convert datetime
    json = {'labels': labels, 'data': data}
    return JsonResponse(json, safe=False)

def historical_graph(request):
    results = dynamodb.get_all_filter("device_values","deviceid_weight")
    labels = []
    data = []
    for x in results:
        y = int(x["value"])
        z = x['datetimeid']
        z = z.split(".")[0]
        z = datetime.strptime(z,"%Y-%m-%dT%H:%M:%S")
        time = "{}:{}:{}".format(str(z.hour).zfill(2),str(z.minute).zfill(2),str(z.second).zfill(2))
        labels.append(time)
        data.append(y)
        #convert datetime
    json = {'labels':labels,'data':data}
    return JsonResponse(json, safe=False)

@csrf_exempt
def inventory_update(request):
    data = request.POST
    item_data = {}
    action = ""
    for x in data:
        if "upc" in x:
            item_data['DT_RowId'] = data[x]
            item_data['upc'] = int(data[x])
        elif "item_desc" in x:
            item_data['item_desc'] = data[x]
        elif "qty" in x:
            item_data['qty'] = int(data[x])
        elif "threshold" in x:
            item_data['threshold'] = int(data[x])
        elif "action" in x:
            action = data[x]
    #action - edit / remove / create
    key = {"upc": item_data['upc']}
    if action == "edit":
        #2 tables upc_product and inventory

        #delete and add

        response_1 = dynamodb.delete("inventory", key)
        response_2 = dynamodb.delete("upc_product", key)

        values = {"upc": item_data["upc"], "item_desc": item_data['item_desc'], "threshold": item_data['threshold']}
        response_3 = dynamodb.add("upc_product", values)
        values = {"upc": item_data['upc'], "qty": item_data['qty']}
        response_4 = dynamodb.add("inventory", values)

        if response_1 and response_2 and response_3 and response_4:
            x = []
            x.append(item_data)
            data = {"data": x}
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse(False)
    elif action == "remove":
        #2 tables upc_product and inventory
        response_1 = dynamodb.delete("inventory",key)
        response_2 = dynamodb.delete("upc_product",key)
        if response_1 and response_2:
            data = {"data":[]}
            return JsonResponse(data,safe=False)
        else:
            return JsonResponse(False)
    elif action == "create":
        #upc_product
        values = {"upc": item_data["upc"], "item_desc": item_data['item_desc'], "threshold": item_data['threshold']}
        response_1 = dynamodb.add("upc_product",values)
        values = {"upc": item_data['upc'], "qty": item_data['qty']}
        response_2 = dynamodb.add("inventory",values)
        if response_1 and response_2:
            x = []
            x.append(item_data)
            data = {"data": x}
            return JsonResponse(data, safe=False)
        else:
            return JsonResponse(False)

    #for x in data:
        #upc = x[0]
        #item_desc = x[1]
        #item_qty = x[2]
        #item_threshold = x[3]
        #item_action = x[4]
    return HttpResponse(data)

def inventory_data(request):
    # fetch inventory list
    response = dynamodb.get_all("inventory")
    # response_2 = dynamodb.get_all("upc_product")
    i = 1
    for x in response:
        # find corresponding upc_product entry
        upc = x['upc']
        result = dynamodb.get("upc_product", {'upc': upc})
        if result:
            x['upc'] = int(x['upc'])
            x['qty'] = int(x['qty'])
            x['item_desc'] = result['item_desc']
            x['threshold'] = int(result['threshold'])
            x['DT_RowId'] = upc
    if response:
        #json = simplejson.dumps(response, use_decimal=True)
        data = {"data":response}
        return JsonResponse(data, safe=False)
    else:
        return JsonResponse(False)


def inventory(request):
    return render(request, 'inventory.html')


def product(request):
    pass

def login_view(request):
    form = LoginForm(request.POST or None)

    msg = None

    if request.method == "POST":

        if form.is_valid():
            username = form.cleaned_data.get("username")
            password = form.cleaned_data.get("password")
            user = authenticate(username=username, password=password)
            if user is not None:
                login(request, user)
                return redirect("/")
            else:    
                msg = 'Invalid credentials'    
        else:
            msg = 'Error validating the form'    

    return render(request, "accounts/login.html", {"form": form, "msg" : msg})

def register_user(request):

    msg     = None
    success = False

    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get("username")
            raw_password = form.cleaned_data.get("password1")
            user = authenticate(username=username, password=raw_password)

            msg     = 'User created - please <a href="/login">login</a>.'
            success = True
            
            #return redirect("/login/")

        else:
            msg = 'Form is not valid'    
    else:
        form = SignUpForm()

    return render(request, "accounts/register.html", {"form": form, "msg" : msg, "success" : success })
