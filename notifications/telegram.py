import requests

def sendTelegramMessage(message, telegram_token, chat_id):
    if not telegram_token or not chat_id:
        print("Telegram token or chat ID is missing.")
        return False

    url = f"https://api.telegram.org/bot{telegram_token}/sendMessage"
    data = {"chat_id": chat_id, "text": message, "parse_mode": "Markdown"}
    
    try:
        response = requests.post(url, data=data)
        if response.status_code == 200:
            print("Message sent successfully!")
            return True
        else:
            print(f"Failed to send message: {response.text}")
            return False
    except requests.RequestException as e:
        print(f"Error while sending Telegram message: {e}")
        return False
