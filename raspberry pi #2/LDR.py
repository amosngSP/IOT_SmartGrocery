
import serial
import sys
from time import sleep
from AWSIoTPythonSDK.MQTTLib import AWSIoTMQTTClient
import json
from datetime import date
import datetime

def customCallback(client, userdata, message):
	print("Received a new message: ")
	print(message.payload)
	print("from topic: ")
	print(message.topic)
	print("--------------\n\n")

host = "a76z46r8md8xy-ats.iot.us-east-1.amazonaws.com"
rootCAPath = "rootca.pem"
certificatePath = "certificate.pem.crt"
privateKeyPath = "private.pem.key"

my_rpi = AWSIoTMQTTClient("BasicLightPubSub")
my_rpi.configureEndpoint(host, 8883)
my_rpi.configureCredentials(rootCAPath, privateKeyPath, certificatePath)

my_rpi.configureOfflinePublishQueueing(-1)  # Infinite offline Publish queueing
my_rpi.configureDrainingFrequency(2)  # Draining: 2 Hz
my_rpi.configureConnectDisconnectTimeout(10)  # 10 sec
my_rpi.configureMQTTOperationTimeout(5)  # 5 sec

# Connect and subscribe to AWS IoT
my_rpi.connect()
my_rpi.subscribe("sensors/light", 1, customCallback)
sleep(2)

while 1:
	ser=serial.Serial("/dev/ttyUSB0",9600)
	b=ser.readline()
	bd=b.decode()
	value = float(bd.rstrip())
	#print("Light value:" + str(value))
	#if value>700.0: 
		#print("Too much light")
	message = {}
	message["deviceid"] = "deviceid_light"
	now = datetime.datetime.now()
	message["datetimeid"] = now.isoformat()      
	message["value"] = value
	my_rpi.publish("sensors/light", json.dumps(message), 1)
	sleep(5) # use this to set interval in seconds

	