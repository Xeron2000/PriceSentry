# core/notifier.py

from utils.send_notifications import send_notifications


class Notifier:
    def __init__(self, config):
        self.notification_channels = config.get("notificationChannels", [])
        self.telegram_config = config.get("telegram", {})
        self.dingding_config = config.get("dingding", {})

    def send(self, message):
        if message:
            send_notifications(
                message,
                self.notification_channels,
                self.telegram_config,
                self.dingding_config,
            )
