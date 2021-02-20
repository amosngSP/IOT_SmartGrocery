#Credits for the BotHandler Class
#https://github.com/magnitopic/YouTubeCode

import requests
class BotHandler:
    token = '1620569172:AAEoFuZf02nunzAHPrUhyt50lGexusDrFIE' #Telegram Bot Token
    def __init__(self):
            self.api_url = "https://api.telegram.org/bot{}/".format(self.token)

    #url = "https://api.telegram.org/bot<token>/"

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

    def send_messages(self,chat_id,text):
        for x in chat_id:
            params = {'chat_id': chat_id, 'text': text, 'parse_mode': 'HTML'}
            method = 'sendMessage'
            resp = requests.post(self.api_url + method, params)
        return True
    def send_image(self,chat_id,text,image):
        params = {'chat_id': chat_id, 'caption': text}
        files = {'photo':image}
        headers = {'content-type':"multipart/form-data"}
        method = 'sendPhoto'
        resp = requests.post(self.api_url + method, files=files,data=params)
        print(resp.content)
        return resp
        
    def get_first_update(self):
        get_result = self.get_updates()

        if len(get_result) > 0:
            last_update = get_result[0]
        else:
            last_update = None

        return last_update

