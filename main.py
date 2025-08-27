import json
import random
import secrets
import string
import threading
import uuid
import logging
from os import system
from time import time
from hashlib import md5
from dataclasses import dataclass
from typing import Dict, List, Tuple
from threading import Thread, Lock
from urllib.parse import urlencode
import requests

from utils.email_api import KopechkaAPI
from signer.sign import sign

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

lock = threading.Lock()

@dataclass
class Config:
    VERSION_LIST = ['32.9.5', '32.7.5', '38.4.3', '38.4.2', '38.4.1', '38.7.1', '38.3.3', '40.8.3']
    DOMAINS = [
        "api16-normal-alisg.tiktokv.com",
        "api16-normal-c-alisg.tiktokv.com",
        "api31-normal-alisg.tiktokv.com",
        "api16-normal-c-useast1a.tiktokv.com",
        "api22-normal-c-useast1a.tiktokv.com",
        "api16-normal-c-useast1a.musical.ly",
        "api19-normal-c-useast1a.musical.ly",
        "api.tiktokv.com"
    ]
    COUNTRIES = ['au', 'kz', 'co']

@dataclass
class Device:
    iid: str
    did: str
    device_type: str
    device_brand: str
    os_version: str
    cdid: str
    openudid: str
    version: str
    sec_token: str
    country: str

    def to_dict(self) -> Dict:
        return {
            'iid': self.iid,
            'did': self.did,
            'device_type': self.device_type,
            'device_brand': self.device_brand,
            'os_version': self.os_version,
            'cdid': self.cdid,
            'openudid': self.openudid,
            'version': self.version,
            'sec_token': self.sec_token,
            'country': self.country
        }

class TikTokAPI:
    def __init__(self, proxy: str):
        self.proxy = {'http': f'http://{proxy}', 'https': f'http://{proxy}'}
        self.session = requests.Session()
        self.session.proxies.update(self.proxy)

    @staticmethod
    def xor(value: str) -> str:
        return "".join([hex(ord(c) ^ 5)[2:] for c in value])

    @staticmethod
    def build_params(device: Device) -> Dict:
        version_code = device.version.replace('.', '0')
        timestamp = str(time() * 1000)[:13]
        timestamp_sec = str(time() * 1000)[:10]

        return {
            'passport-sdk-version': '19',
            'iid': device.iid,
            'device_id': device.did,
            'ac': 'wifi',
            'channel': 'googleplay',
            'aid': '1233',
            'app_name': 'musical_ly',
            'version_code': version_code,
            'version_name': device.version,
            'device_platform': 'android',
            'os': 'android',
            'ab_version': device.version,
            'ssmix': 'a',
            'device_type': device.device_type,
            'device_brand': device.device_brand,
            'language': device.country.lower(),
            'os_api': '25',
            'os_version': device.os_version,
            'openudid': device.openudid,
            'manifest_version_code': f'202{version_code}0',
            'resolution': '1467*720',
            'dpi': '300',
            'update_version_code': f'202{version_code}0',
            '_rticket': timestamp,
            'is_pad': '0',
            'app_type': 'normal',
            'sys_region': device.country.upper(),
            'mcc_mnc': '50514',
            'timezone_name': 'Australia/Sydney',
            'ts': timestamp_sec,
            'timezone_offset': '-37800',
            'build_number': device.version,
            'region': device.country.upper(),
            'carrier_region': device.country.upper(),
            'uoo': '0',
            'app_language': device.country.lower(),
            'op_region': device.country.upper(),
            'ac2': 'wifi',
            'host_abi': 'armeabi-v7a',
            'cdid': device.cdid,
            'support_webview': '1',
            'reg_store_region': device.country.lower(),
            'okhttp_version': '4.2.137.40-tiktok',
            'use_store_region_cookie': '1'
        }

    @staticmethod
    def build_headers(device: Device, payload: str, sig: dict, dm_status: str = "login=0;ct=0;rt=9") -> Dict:
        version_code = device.version.replace('.', '0')
        return {
            'accept-encoding': 'gzip',
            'connection': 'Keep-Alive',
            'content-type': 'application/x-www-form-urlencoded; charset=UTF-8',
            'passport-sdk-version': '19',
            'sdk-version': '2',
            'user-agent': f'com.zhiliaoapp.musically/202{version_code}0 (Linux; U; Android {device.os_version}; en_{device.country.upper()}; {device.device_type}; Build/RP1A.200720.012;tt-ok/3.12.13.4-tiktok)',
            'x-ss-req-ticket': str(time() * 1000)[:13],
            'x-ss-stub': md5(payload.encode('utf-8')).hexdigest().upper(),
            'x-tt-bypass-dp': '1',
            'x-tt-dm-status': dm_status,
            'x-vc-bdturing-sdk-version': '2.3.4.i18n',
            'X-Ladon': sig['X-Ladon'],
            'X-Khronos': str(sig['X-Khronos']),
            'X-Argus': sig['X-Argus'],
            'X-Gorgon': sig['X-Gorgon']
        }

    def send_code(self, domain: str, email: str, password: str, device: Device) -> Tuple[requests.Response, str]:
        params = self.build_params(device)
        params_str = urlencode(params)

        payload_data = {
            'password': self.xor(password),
            'rule_strategies': '2',
            'mix_mode': '1',
            'multi_login': '1',
            'email': self.xor(email),
            'account_sdk_source': 'app',
            'type': '34'
        }
        payload = urlencode(payload_data)

        sig = sign(params_str, payload, device.sec_token, None, 1233)
        headers = self.build_headers(device, payload, sig)

        response = self.session.post(f'https://{domain}/passport/email/send_code/?{params_str}', headers=headers, data=payload)
        return response, params_str

    def verify_code(self, domain: str, email: str, code: str, device: Device) -> requests.Response:
        params = self.build_params(device)
        params_str = urlencode(params)

        payload_data = {
            'birthday': f"{random.randint(1990, 2002)}-0{random.randint(1, 9)}-{random.randint(10, 25)}",
            'code': code,
            'account_sdk_source': 'app',
            'mix_mode': '1',
            'multi_login': '1',
            'type': '34',
            'email': self.xor(email)
        }
        payload = urlencode(payload_data)

        url = f'https://{domain}/passport/email/register_verify_login/?{params_str}'
        sig = sign(params_str, payload, device.sec_token, None, 1233)
        headers = self.build_headers(device, payload, sig, dm_status="login=1;ct=1;rt=8")

        response = self.session.post(url, headers=headers, data=payload)
        return response

class AccountCreator:
    def __init__(self, devices: List[str], models: List[str], proxies: List[str]):
        self.devices = devices
        self.models = models
        self.proxies = proxies
        self.lock = Lock()

    def generate_device(self) -> Device:
        device_data = random.choice(self.devices).split(':')
        os_version = f"{random.randint(7, 33)}.{random.randint(0, 9)}.{random.randint(0, 9)}"
        sec_token = "A6RDV9Pib_ZYqYnv" + ''.join(secrets.choice(string.ascii_letters + string.digits) for _ in range(9))

        return Device(
            iid=device_data[0],
            did=device_data[1],
            device_type=device_data[2],
            device_brand=device_data[3],
            os_version=os_version,
            cdid=str(uuid.uuid4()),
            openudid=secrets.token_hex(8),
            version=random.choice(Config.VERSION_LIST),
            sec_token=sec_token,
            country=random.choice(Config.COUNTRIES)
        )

    @staticmethod
    def generate_credentials() -> str:
        password = f"{secrets.token_hex(random.randint(4, 6))}{random.randint(10000, 99999)}!"
        return password

    def create_account(self) -> None:
        try:
            proxy = random.choice(self.proxies)
            api = TikTokAPI(proxy)
            email_api = KopechkaAPI(kopechka_key)

            email, order_id = email_api.create_order('mail.com', 'tiktok.com')
            password = self.generate_credentials()

            device = self.generate_device()
            domain = random.choice(Config.DOMAINS)

            response, params_str = api.send_code(domain, email, password, device)

            if 'success' in response.text:
                logger.info(f"Wait code {email}")

                code = email_api.get_messages(order_id)
                email_api.cancel_order(order_id)

                if code:
                    logger.info(f"Code: {code}")

                    response = api.verify_code(domain, email, code, device)
                    data = response.json()

                    if "session_key" in response.text:
                        account_info = data["data"]
                        headers = response.headers

                        tt_token = headers["X-Tt-Token"]
                        multi_sids = headers["X-Tt-Multi-Sids"]
                        lanusk = headers.get("X-Bd-Lanusk", "")
                        sessionid = account_info["session_key"]
                        username = account_info["screen_name"]

                        account_data = {
                            'account': f'{username}:{password}:{email}',
                            'sessionid': sessionid,
                            'tt-token': tt_token,
                            'sids': multi_sids,
                            'lanusk': lanusk,
                            'device': device.to_dict()
                        }

                        with lock:
                            open("accounts.txt", "a+").write(json.dumps(account_data) + "\n")
                            logger.info(f"[{username}:{password}] Account created")
                    else:
                        error_code = data.get("data", {}).get("error_code", "Unknown")
                        logger.warning(f"Account could not be opened. Error code: {error_code}")
                else:
                    logger.warning("Not mail code")
            else:
                logger.warning(f"Failed send code {email}")
        except Exception as e:
            logger.error(f"Error creating account: {e}")

    def run(self, threads: int):
        for _ in range(threads):
            Thread(target=self.worker).start()

    def worker(self):
        while True:
            self.create_account()

def load_data(filename: str) -> List[str]:
    try:
        with open(filename, "r", encoding="utf-8") as f:
            return f.read().splitlines()
    except FileNotFoundError:
        logger.error(f"File not found: {filename}")
        return []

def main():
    system("title TikTok Creator ^| @hiddenexe & cls")

    devices = load_data("data/devices.txt")
    models = load_data("data/models.txt")
    proxies = load_data("data/proxy.txt")

    threads = int(input("Thread count: "))
    creator = AccountCreator(devices, models, proxies)
    creator.run(threads)

if __name__ == '__main__':
    kopechka_key = 'api_key' # https://www.kopechka.com/
    main()

