import time
import hmac
import hashlib
import base64
import urllib.parse
import requests

def sendDingDingMessage(message, webhook_url, secret=None):
    if not webhook_url:
        print("DingDing webhook URL is missing.")
        return False

    timestamp = str(round(time.time() * 1000))
    sign = ""
    if secret:
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"), string_to_sign.encode("utf-8"), digestmod=hashlib.sha256
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    headers = {"Content-Type": "application/json"}
    payload = {
        "msgtype": "text",
        "text": {"content": message}
    }

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        if response.status_code == 200:
            print("Message sent to dingding successfully!")
            return True
        else:
            print(f"Failed to send message: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error while sending DingDing message: {e}")
        return False
