# core/notifier.py

from utils.sendNotifications import sendNotifications


class Notifier:
    def __init__(self, config):
        self.notification_channels = config.get("notificationChannels", [])
        self.telegram_config = config.get("telegram", {})
        self.dingding_config = config.get("dingding", {})

    def send(self, message):
        if message:
            sendNotifications(
                message,
                self.notification_channels,
                self.telegram_config,
                self.dingding_config,
            )
