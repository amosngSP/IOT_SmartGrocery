from api import barcode_reader, UPC_lookup, add_if_not_exist_item, add_deduct_item, Dynamodb
import boto3
from time import sleep
from gpiozero import Buzzer
import signal
bz = Buzzer(5)
#infinite while loop
dynamodb = Dynamodb()

class TimeOutException(Exception):
   pass
 
def alarm_handler(signum, frame):
    print("ALARM signal received")
    raise TimeOutException()

while True:
    try:
        #check status of the mode
        Key = {'id':1}
        result = dynamodb.get('barcode_status',Key)
        mode = ""
        if result:
            #0 - deduct mode, 1 - add mode
            mode = result['b_mode']
            print(mode)
        else:
            print("Error! Can't fetch data from DynamoDB")
            break
        
        try:
            signal.signal(signal.SIGALRM, alarm_handler)
            signal.alarm(3)
            value = barcode_reader()
            signal.alarm(0)
        except:
            value = False
        if value:
            value = int(value)
        else:
            value = ""
        
        if value != "":
            #check if product exists in DynamoDB
            check = add_if_not_exist_item(value)
            if check:
                #product exist
                #let us go ahead and add/deduct
                add_deduct_item(value,mode)
            else:
                bz.on()
                sleep(1)
                bz.off()
                print("Item cannot be found!")
        sleep(1)
    except KeyboardInterrupt:
        print("Program Closing")
        break
