# core/notifier.py

from utils.send_notifications import send_notifications


class Notifier:
    def __init__(self, config):
        self.notification_channels = config.get("notificationChannels", [])
        self.telegram_config = config.get("telegram", {})

    def send(
        self, message, image_bytes=None, image_caption=None
    ):
        if message and message.strip():
            try:
                send_notifications(
                    message,
                    self.notification_channels,
                    self.telegram_config,
                    image_bytes=image_bytes,
                    image_caption=image_caption,
                )
            except Exception as e:
                # Log the error but don't raise it
                print(f"Error sending notification: {e}")
