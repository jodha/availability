from __future__ import annotations

import os
from functools import lru_cache


class Settings:
    def __init__(self) -> None:
        self.secret_key = os.environ["SECRET_KEY"]
        self.admin_username = os.environ["ADMIN_USERNAME"]
        self.admin_password = os.environ["ADMIN_PASSWORD"]
        self.invite_code = os.environ["INVITE_CODE"]
        self.database_url = os.environ["DATABASE_URL"]
        self.smtp_host = os.environ["SMTP_HOST"]
        self.smtp_port = int(os.environ["SMTP_PORT"])
        self.smtp_user = os.environ["SMTP_USER"]
        self.smtp_password = os.environ["SMTP_PASSWORD"]
        self.smtp_from = os.environ["SMTP_FROM"]
        self.timezone = os.environ["TIMEZONE"]
        self.max_events_per_poll = int(os.environ["MAX_EVENTS_PER_POLL"])
        self.app_name = os.environ["APP_NAME"]
        self.base_url = os.environ["BASE_URL"]


@lru_cache
def get_settings() -> Settings:
    return Settings()
