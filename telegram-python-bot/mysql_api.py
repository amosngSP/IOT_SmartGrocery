import mysql.connector
import datetime
import decimal
import sys
import json
from flask import jsonify
import numpy

class GenericEncoder(json.JSONEncoder):

    def default(self,obj):
        if isinstance(obj, numpy.generic):
            return numpy.asscaler(obj)
        elif isinstance(obj, datetime.datetime):
            return obj.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(obj, decimal.Decimal):
            return float(obj)
        else:
            return json.JSONEncoder.default(self,obj)

website = "http://10.10.10.161:8001"
videopath = "/home/pi/Desktop/IOT PROJ/Videos"
class Database():
    username = 'root'
    password = 'P@ssw0rd'
    host = '10.10.10.161'
    database = 'iot'
    cnx = None
    cursor = None
    def __init__(self):
        try:
            self.cnx = mysql.connector.connect(user=self.username,password=self.password,host=self.host,database=self.database)
            self.cursor = self.cnx.cursor()
        except:
            print("Unable to connect to database!")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
        
    def select_one_row(self,sql):
        try:
            self.cursor.execute(sql)
            entry = self.cursor.fetchone()
            self.cnx.commit()
            return entry
        except:
            print("Program Failure!")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return None

    def select_rows(self,sql):
        try:
            self.cursor.execute(sql)
            entry = self.cursor.fetchall()
            self.cnx.commit()
            return entry
        except:
            print("Program Failure!")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return None

    def insert_update(self,sql):
        try:
            self.cursor.execute(sql)
            self.cnx.commit()
            return True
        except:
            print("Program Failure!")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return False

    def verify(self,username,password):
        try:
            sql = "SELECT * FROM users WHERE username = '{}' AND password = '{}'".format(username,password)
            return self.select_one_row(sql)
        except:
            print("Program Failure!")
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return False

    def get_subscribers_list(self):
        try:
            sql = "SELECT chat_id FROM subscribe WHERE subscribe='1'"
            subscribers = []
            entry = self.select_rows(sql)
            for x in entry:
                subscribers.append(x[0])
            return subscribers;
        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return None
        
    def fetch_fromdb_as_json(self,sql):
        try:
            self.cursor.execute(sql)
            row_headers=[x[0] for x in self.cursor.description] 
            results = self.cursor.fetchall()
            data = []
            for result in results:
                data.append(dict(zip(row_headers,result)))
            
            data_reversed = data[::-1]

            data = {'data':data_reversed}

            return self.data_to_json(data)

        except:
            print(sys.exc_info()[0])
            print(sys.exc_info()[1])
            return None

    def data_to_json(self,data):
        json_data = json.dumps(data,cls=GenericEncoder)
        return json_data

    def close(self):
        self.cursor.close()
        self.cnx.close()
