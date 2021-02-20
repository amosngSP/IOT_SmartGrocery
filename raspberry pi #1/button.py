from gpiozero import LED, Button
from signal import pause
import sys
from time import sleep
from api import Dynamodb

dynamodb = Dynamodb()
led_green = LED(26)
led_red = LED(20)
button = Button(19,pull_up=False)

def toggle_state(led):
    #to pass in led_green
    if led.is_lit:
        #gre
        ExpressionAttributeValues={':val1':1}
    else:
        ExpressionAttributeValues={':val1':0}
    Key = {'id': 1}
    UpdateExpression = 'SET b_mode = :val1'
    dynamodb.update('barcode_status',Key,UpdateExpression,ExpressionAttributeValues)
        

while True:
    try:
        #check current mode in database
        #0 - deduct mode
        #1 - add mode
        Key = {'id':1}
        result = dynamodb.get('barcode_status',Key)
        if result:
            mode = result['b_mode']
            if mode == 0:
                led_red.on()
                led_green.off()
            else:
                led_green.on()
                led_red.off()
        button.wait_for_press(timeout=5)
        if button.is_pressed:
            print("Button pressed!")
            if led_green.is_lit:
                led_green.off()
                led_red.on()
            else:
                led_green.on()
                led_red.off()
            toggle_state(led_green)
            sleep(1)
    except KeyboardInterrupt:
        led_green.off()
        led_red.off()
        print("Closing")
        break
