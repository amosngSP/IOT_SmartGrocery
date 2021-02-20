import boto3
import botocore
from picamera import PiCamera
from time import sleep
import os
from api import Dynamodb
from gpiozero import LED
import re


# Set the filename and bucket name
BUCKET = 'imageawsbucket'  # replace with your own unique bucket name
location = {'LocationConstraint': 'us-east-1'}
file_path = '/home/pi/Desktop'
file_name = 'image.jpg'
dynamodb = Dynamodb()
led = LED(18)
camera = PiCamera()

def onLED():
	led.on()

def offLED():
	led.off()

def takePhoto():
	if os.path.exists(file_path + "/" + file_name):
		os.remove(file_path + "/" + file_name)
	sleep(2)
	onLED()
	sleep(1)
	camera.capture(file_path + "/" + file_name)
	offLED()
	return

def uploadToS3(file_path, file_name, bucket_name, location):
	s3 = boto3.resource('s3')  # Create an S3 resource
	exists = True

	try:
		s3.meta.client.head_bucket(Bucket=bucket_name)
	except botocore.exceptions.ClientError as e:
		error_code = int(e.response['Error']['Code'])
		if error_code == 404:
			exists = False
		
	if exists == False:
		s3.create_bucket(Bucket=bucket_name,
						 CreateBucketConfiguration=location)

	# Upload the file
	full_path = file_path + "/" + file_name
	s3.Object(bucket_name, file_name).put(Body=open(full_path, 'rb'))
	print("File uploaded")


def detect_labels(bucket_name, key, max_labels=10, min_confidence=95, region="us-east-1"):
	rekognition = boto3.client("rekognition", region)
	response = rekognition.detect_labels(
		Image={
			"S3Object": {
				"Bucket": bucket_name,
				"Name": key,
			}
		},
		MaxLabels=max_labels,
		MinConfidence=min_confidence,
	)
	listdontupdate=[]
	items = [] 
	items = dynamodb.get_all("upc_product")
	
	for label in response['Labels']:
		print ("Label: " + label['Name'])
		#print ("Confidence: " + str(label['Confidence']))
		print ("Number of instances:" +  str(len(label['Instances'])))
		expression = "SET qty = :val"
		values = {':val':len(label['Instances'])}
		#print(items)
		for i in items:
			key={"upc": i['upc']}
			if label['Name'] == i['item_desc']:
				dynamodb.update("inventory",key,expression,values)		
				print("Database Updated")
				listdontupdate.append(i['upc'])
	
	#update everything else in the fridge to 0
	for i in items:
		if re.search("[8]{6,6}\\d{7,7}",str(i['upc'])) is not None:
			if i['upc'] not in listdontupdate:
				expression = "SET qty = :val"
				values = {':val': '0'}
				key={"upc": i['upc']}
				dynamodb.update("inventory",key,expression,values)
				print("extras updated")

		#for instance in label['Instances']:
		#	print (" Bounding box")
		#	print (" Top: " + str(instance['BoundingBox']['Top']))
		#	print (" Left: " + str(instance['BoundingBox']['Left']))
		#	print (" Width: " + str(instance['BoundingBox']['Width']))
		#	print (" Height: " + str(instance['BoundingBox']['Height']))
		#	print (" Confidence: " + str(instance['Confidence']))
		#	print()

while 1:
	takePhoto()
	uploadToS3(file_path,file_name, BUCKET, location)
	detect_labels(BUCKET, file_name)
	sleep(3) # if not testing set to 60 or longer

	#for label in detect_labels(BUCKET, file_name):
	#	print("{Name} - {Confidence}%".format(**label))
	#	if label["Confidence"] >= highestconfidence:
	#		highestconfidence = label["Confidence"]
	#		best_bet_item = label["Name"]
