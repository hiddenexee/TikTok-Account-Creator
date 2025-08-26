import time
import secrets
import requests


class KopechkaAPI:
    def __init__(self, api_key):
        self.base_url = 'https://api.kopechka.com/api/v1'
        self.headers = {
            'X-API-Key': api_key,
            'Content-Type': 'application/json'
        }

    def get_balance(self):
        response = requests.get(f'{self.base_url}/balance', headers=self.headers)
        return response.json()

    def create_order(self, domain, site):
        while True:
            try:
                data = {'domain': domain, 'site': site}
                response = requests.post(f'{self.base_url}/orders', json=data, headers=self.headers).json()

                try:
                    data = response['data']

                    return data["email"], data['orderId']
                except:
                    print(response)
            except Exception:
                pass
            time.sleep(3)

    def get_messages(self, order_id):
        for _ in range(7):
            try:
                response = requests.get(f'{self.base_url}/orders/{order_id}/messages', headers=self.headers).json()

                messages = response['messages']
                if len(messages) > 0:
                    title = messages[0]['title'].split(' ')[0]
                    return title
            except:
                pass
            time.sleep(5)
        else:
            return None

    def cancel_order(self, order_id):
        response = requests.delete(f'{self.base_url}/orders/{order_id}', headers=self.headers)
        return response.json()
