#! /usr/bin/python2
# coding: utf-8
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import time
import sys
import mysql.connector
from time import sleep
from datetime import date
import datetime
import RPi.GPIO as GPIO
from gpiozero import LED
from twilio.rest import Client
import json
from api import Dynamodb

dynamodb = Dynamodb()

def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

# Set up for the HX711 module
EMULATE_HX711=False

referenceUnit = 479

if not EMULATE_HX711:
	import RPi.GPIO as GPIO
	from hx711 import HX711
else:
	from emulated_hx711 import HX711

# Assigning GPIO pins to the hardware
# GPIO: 5 dout purple
# 13 pd_sck yellow

hx = HX711(5, 6)
hx.set_reading_format("MSB", "MSB")

# The ‘referenceUnit’ in this project is set to 479 to read the weight accurately.
# First set it to 1 then get the readings of the weight on the sensor of any object
# Based on the reading shown, divide by the actual weight of the object which will be the value of the ‘referenceUnit’

hx.set_reference_unit(referenceUnit)

hx.reset()
print('Wait for the message to say that the tare is done before placing the water bottle on the sensor')
hx.tare()

print("Tare done! You may place the object now")
# Giving the user time to put the bottle on the scale
sleep(5)
	
host = "a76z46r8md8xy-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("BasicWeightPubSub")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("sensors/weight", 1, customCallback)
sleep(2)

try:
	while 1:
		# Getting the weight 
		val = hx.get_weight(5)
		hx.power_down()
		hx.power_up()
		message = {}
		message["deviceid"] = "deviceid_weight"
		now = datetime.datetime.now()
		message["datetimeid"] = now.isoformat()      
		message["value"] = val
		my_rpi.publish("sensors/weight", json.dumps(message), 1)
		sleep(5) # use this to set interval in seconds
		
		items = [] 
		items = dynamodb.get_all("upc_product")
		expression = "SET qty = :val"
		values = {':val':val}
		#print(items)
		for i in items:
			#print(i['upc'])
			if i['item_desc']=="Rice":
				key={"upc": i['upc']}
				dynamodb.update("inventory",key,expression,values)
				print("Database Updated")
except:
	print("program terminated")    
