import os
import secrets
from pathlib import Path

from envparse import env

from app.utils import cli

env.read_envfile(cli.CONFIG_FILE)


def get_project_root() -> Path:
    return Path(__file__).parent.parent


local_dir = get_project_root()  # каталог с ботом

TELEGRAM_TOKEN = env.str("TELEGRAM_TOKEN", default="")
BOT_PUBLIC_PORT = env.int("BOT_PUBLIC_PORT", default=8080)
LOGS_BASE_PATH = env.str("LOGS_BASE_PATH", default="logs")
SKIP_UPDATES = env.bool("SKIP_UPDATES", default=False)

DOMAIN = env.str("DOMAIN", default="example.com")
SECRET_KEY = secrets.token_urlsafe(48)
WEBHOOK_BASE_PATH = env.str("WEBHOOK_BASE_PATH", default="/tg/webhook")
WEBHOOK_PATH = f"{WEBHOOK_BASE_PATH}/{SECRET_KEY}"
WEBHOOK_URL = f"https://{DOMAIN}{WEBHOOK_PATH}/{TELEGRAM_TOKEN}"
CHECK_IP = env.bool("CHECK_IP", default=False)

POSTGRES_HOST = env.str("POSTGRES_HOST", default="localhost")
POSTGRES_PORT = env.int("POSTGRES_PORT", default=5432)
POSTGRES_PASSWORD = env.str("POSTGRES_PASSWORD", default="")
POSTGRES_USER = env.str("POSTGRES_USER", default="postgres")
POSTGRES_DB = env.str("POSTGRES_DB", default="forge")
POSTGRES_URI = f"postgres://{POSTGRES_USER}:{POSTGRES_PASSWORD}@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"

ADMIN = env.str("ADMIN", default="iambrock")
START_ATTEMPTS = env.int("START_ATTEMPTS", default=3)
ATTEMPTS_FOR_REFERAL = env.int("ATTEMPTS_FOR_REFERAL", default=2)

IMAGE_PATH = env.str("IMAGE_PATH", default="data/image")
FONT_PATH = env.str("FONT_PATH", default="data/fonts")
TEMP_PATH = env.str("TEMP_PATH", default="data/tempfiles")

BOT_NAME = "Api4chbot"  # имя бота
GROUPS_DICT = {
    "Group name": "ggffddsa"
}  # список групп для вступления в формате {'Имя на кнопке': 'имя группы после @'}
"""psql -h localhost -U admin textimage_db"""
