# core/notifier.py

import base64
import time
from typing import Any, Dict, Optional

from core.api import update_api_data
from utils.send_notifications import send_notifications


class Notifier:
    def __init__(self, config):
        self.notification_channels = config.get("notificationChannels", [])
        self.telegram_config = config.get("telegram", {})

    def update_config(self, config) -> None:
        """Refresh notifier settings after configuration hot reload."""
        self.notification_channels = config.get("notificationChannels", [])
        self.telegram_config = config.get("telegram", {})

    def send(
        self,
        message: str,
        image_bytes: Optional[bytes] = None,
        image_caption: Optional[str] = None,
        chart_metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        if not message or not message.strip():
            return

        try:
            send_notifications(
                message,
                self.notification_channels,
                self.telegram_config,
                image_bytes=image_bytes,
                image_caption=image_caption,
            )
        except Exception as exc:
            # Log the error but don't raise it
            print(f"Error sending notification: {exc}")

        if image_bytes is None:
            return

        try:
            encoded_image = base64.b64encode(image_bytes).decode("ascii")
            metadata: Dict[str, Any] = dict(chart_metadata or {})
            metadata.setdefault("generatedAt", time.time())
            update_api_data(chart_image={"imageBase64": encoded_image, "metadata": metadata})
        except Exception as exc:
            print(f"Failed to persist chart preview for dashboard: {exc}")
