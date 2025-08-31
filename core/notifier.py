# core/notifier.py

from utils.send_notifications import send_notifications


class Notifier:
    def __init__(self, config):
        self.notification_channels = config.get("notificationChannels", [])
        self.telegram_config = config.get("telegram", {})
        self.dingding_config = config.get("dingding", {})

    def send(
        self, message, image_bytes=None, image_caption=None, dingding_image_url=None
    ):
        if message and message.strip():
            try:
                send_notifications(
                    message,
                    self.notification_channels,
                    self.telegram_config,
                    self.dingding_config,
                    image_bytes=image_bytes,
                    image_caption=image_caption,
                    dingding_image_url=dingding_image_url,
                )
            except Exception as e:
                # Log the error but don't raise it
                print(f"Error sending notification: {e}")
