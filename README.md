# IOT_SmartGrocery
Internet of Things Project - Smart Grocery

Steps to take: 
1) Setup 2 Raspberry Pi according to the fritzing diagrams below
![alt text](https://github.com/amosngSP/IOT_SmartGrocery/tree/main/Misc%20Assets/frit1.JPG?raw=true)
2) In this Raspberry Pi, there is another hx711 sensor. It can be patched by: VCC pin to 5V, GND pin to GND, DT pin to GPIO5 and SCK pin to GPIO6. 

![alt text](https://github.com/amosngSP/IOT_SmartGrocery/tree/main/Misc%20Assets/frit2.JPG?raw=true)

3) On both Raspberry Pi, do the following: 
  - create a file called "requirements.txt"
  - put the following into the file: Asgiref
                                     autopep8
                                     django==2.2.10
                                     pycodestyle
                                     pytz
                                     sqlparse
                                     Unipath
                                     dj-database-url
                                     python-decouple
                                     gunicorn
                                     whitenoise
                                     boto3
                                     simplejson
                                     requests

4) Save the file and execute "pip3 install -r requirements.txt"
5) Execute "sudo raspi-config". Go to interface setttings and inteface options -> enable Serial User need to check what interface the barcode is on. it might be on /dev/hidraw0 or /dev/hidraw1 or in some cases /dev/hidraw2 . User need to then go to line 118 of api.py and edit accordingly.
6) Open Arduino IDE and upload "capture_light.ino" 
7) Execute the following files in different terminals on the 1st Raspberry Pi: weight.py, LDR.py, picam_rekognition.py
8) Execute the following on the 2nd Raspberry Pi: “python manage.py makemigrations” and “python manage.py migrate”
9) On the 2nd Raspberry Pi, execute “python manage.py runserver” to start the web application. To specify port number, add 0.0.0.0:<port_no> at the end.
10) Execute "telegram_app.py" for Telegram Bot.

