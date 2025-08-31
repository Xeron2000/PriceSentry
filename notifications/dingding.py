import base64
import hashlib
import hmac
import time
import urllib.parse

import requests


def send_dingding_message(message, webhook_url, secret=None):
    if not webhook_url:
        print("DingDing webhook URL is missing.")
        return False

    timestamp = str(round(time.time() * 1000))
    sign = ""
    if secret:
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    headers = {"Content-Type": "application/json"}
    payload = {"msgtype": "text", "text": {"content": message}}

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                return True
            else:
                print(f"DingDing API error: {result.get('errmsg', 'Unknown error')}")
                return False
        else:
            print(f"Failed to send message: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error while sending DingDing message: {e}")
        return False


def send_dingding_photo(
    caption, webhook_url, secret=None, image_bytes=None, image_url=None
):
    """
    Send a photo with optional caption to DingDing.
    If image is too large, send as text message with caption only.

    Args:
        caption (str): Caption text for the image
        webhook_url (str): DingDing webhook URL
        secret (str, optional): Secret for signature verification
        image_bytes (bytes, optional): Image bytes (not used due to size limits)
        image_url (str, optional): Public URL of the image (not used due to size limits)

    Returns:
        bool: True on success
    """
    if not webhook_url:
        print("DingDing webhook URL is missing.")
        return False

    # 钉钉有20KB的消息体大小限制，大图片会导致失败
    # 这里我们只发送文本消息，避免大小限制问题
    timestamp = str(round(time.time() * 1000))
    sign = ""
    if secret:
        string_to_sign = f"{timestamp}\n{secret}"
        hmac_code = hmac.new(
            secret.encode("utf-8"),
            string_to_sign.encode("utf-8"),
            digestmod=hashlib.sha256,
        ).digest()
        sign = urllib.parse.quote_plus(base64.b64encode(hmac_code))
        webhook_url = f"{webhook_url}&timestamp={timestamp}&sign={sign}"

    headers = {"Content-Type": "application/json"}

    # 只发送文本消息，避免图片大小限制
    final_message = f"{caption}\n\n📊 图表已生成（请查看Telegram获取详细图表）"

    payload = {"msgtype": "text", "text": {"content": final_message}}

    try:
        response = requests.post(webhook_url, json=payload, headers=headers)
        if response.status_code == 200:
            result = response.json()
            if result.get("errcode") == 0:
                return True
            else:
                print(
                    f"DingDing photo API error: {result.get('errmsg', 'Unknown error')}"
                )
                return False
        else:
            print(f"Failed to send photo message: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error while sending DingDing photo message: {e}")
        return False
