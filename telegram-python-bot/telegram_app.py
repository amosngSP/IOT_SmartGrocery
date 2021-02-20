import requests
import datetime
from api import Dynamodb, website
from bothandler import BotHandler
import boto3
dynamodb = Dynamodb()
iot_bot = BotHandler()

def subscribe(chatid):
    key = {"chat_id":chatid}
    result = dynamodb.get("subscribe",key)
    if result:
        #get subscriber status
        subscribe = result['s_status']
        if subscribe == 1:
            return "Already Subscribed!"
        else:
            #change status
            values = {":stat":1}
            upd_expression = "SET s_status = :stat"
            resp = dynamodb.update("subscribe",key,upd_expression,values)
            if resp:
                return "Status changed to subscribed!"
            else:
                return "An error occurred!"
    else:
        #not in table, add a new entry
        values = {"chat_id":chatid,"s_status":1}
        resp = dynamodb.add("subscribe",values)
        if resp:
            return "Added to the subscriber list!"
        else:
            return "An error occurred!"
            

        
    
def unsubscribe(chatid):
    key = {"chat_id":chatid}
    result = dynamodb.get("subscribe",key)
    if result:
        #user in database
        subscribe = result['s_status']
        if subscribe == 0:
            return "Already Not Subscribed!"
        else:
            values = {":stat":0}
            upd_expression = "SET s_status = :stat"
            resp = dynamodb.update("subscribe",key,upd_expression,values)
            if resp:
                return "Status changed to unsubscribed!"
            else:
                return "An error occurred!"
    else:
        return "You have not subscribed before!"

def toggle_barcode_status():
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
            if mode == 0:
                return "Barcode Scanner now in deduct mode!"
            else:
                return "Barcode Scanner now in add mode!"
        else:
            return "An error occurred!"
    
def grocery_list():
    #fetch from inventory
    #compare with threshold value in upc_product
    inventory = dynamodb.get_all("inventory")
    items = ""
    for x in inventory:
        #fetch the threshold value
        upc = x['upc']
        qty = int(x['qty'])
        upc_product = dynamodb.get("upc_product", {"upc": upc})
        threshold_value = int(upc_product['threshold'])
        item_desc = upc_product['item_desc']
        if qty <= threshold_value:
            x = "Item Description: {}, Quantity Left: {}".format(item_desc,qty)
            items = "{}{}\n".format(items,x)
    return items
def fridgeimage():
    s3 = boto3.client("s3")
    x = s3.get_object(Bucket="imageawsbucket",Key="image.jpg")
    image = x['Body'].read()
    return image
def main():
    new_offset = 0
    print("Telegram bot launching...")
    while True:
        all_updates=iot_bot.get_updates(new_offset)
        
        if len(all_updates) > 0:
            for current_update in all_updates:
                first_update_id = current_update['update_id']
                if 'text' not in current_update['message']:
                    first_chat_text='New member'
                else:
                    first_chat_text = current_update['message']['text']
                first_chat_id = current_update['message']['chat']['id']
                if 'first_name' in current_update['message']:
                    first_chat_name = current_update['message']['chat']['first_name']
                elif 'new_chat_member' in current_update['message']:
                    first_chat_name = current_update['message']['new_chat_member']['username']
                elif 'from' in current_update['message']:
                    first_chat_name = current_update['message']['from']['first_name']
                else:
                    first_chat_name = "unknown"
                
                if first_chat_text == "/togglestate":
                    new_offset = first_update_id + 1
                    iot_bot.send_message(first_chat_id, toggle_barcode_status())
                elif first_chat_text == "/website":
                    new_offset = first_update_id + 1
                    iot_bot.send_message(first_chat_id, website)
                elif first_chat_text == "/subscribe":
                    new_offset = first_update_id + 1
                    iot_bot.send_message(first_chat_id, subscribe(first_chat_id))
                elif first_chat_text == "/unsubscribe":
                    new_offset = first_update_id + 1
                    iot_bot.send_message(first_chat_id, unsubscribe(first_chat_id))
                elif first_chat_text == "/grocerylist":
                    new_offset = first_update_id + 1
                    iot_bot.send_message(first_chat_id, grocery_list())
                elif first_chat_text == "/fridgeimage":
                    new_offset = first_update_id + 1
                    iot_bot.send_message(first_chat_id, "Image coming your way, hang tight!")
                    iot_bot.send_image(first_chat_id, "Image of Fridge",fridgeimage())
                    print("After")
if __name__ == '__main__':
    try:
        main()
    except KeyboardInterrupt:
        exit()
