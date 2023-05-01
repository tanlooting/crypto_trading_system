import requests

class Alerts:
    def __init__(self, 
                 tg_chat_id: str , 
                 tg_api_token: str, 
                 email_recipient: list = None):
        self.chat_id = tg_chat_id
        self.api_token = tg_api_token
        self.email_recipients = email_recipient
    
    def send_telegram_message(self, message):
        
        data_dict = {
            'chat_id': str(self.chat_id),
            'text': str(message),
            'parse_mode': 'markdown',
            'disable_notification': False,
            }
        url = f'https://api.telegram.org/bot{self.api_token}/sendMessage'
        response = requests.post(url, json=data_dict)
        return response
    
    def send_email(self, message):
        """Not implemented yet"""
        ... 
