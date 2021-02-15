import logging

from tortoise import Tortoise, generate_config

from app import env

from app.models.users import Users


def describe_credentials(models):
    described_models: dict = generate_config(env.POSTGRES_URI, models)
    for database in described_models.get("connections"):
        source_pass = env.POSTGRES_PASSWORD
        hided_pass = source_pass[0] + "*" * len(source_pass[1:-1]) + source_pass[-1]
        described_models["connections"][database]["credentials"]["password"] = hided_pass

    return described_models


async def init_db():
    """Инициаоизация базы днных"""
    tortoise_logger = logging.getLogger("tortoise")
    tortoise_logger.setLevel("CRITICAL")

    modules = {"models": [f"app.models.{item}" for item in ["settings", "users", "category", "mail", "pics", "promo"]]}
    await Tortoise.init(
        db_url=env.POSTGRES_URI, modules=modules,
    )
    await Tortoise.generate_schemas()
    logging.info("PostgreSQL Connection opened")
    logging.info(describe_credentials(modules))


async def get_user_row(u_id):
    """Возвращает пользователя из бд"""
    return await Users.filter(user_id=u_id).first()


async def create_new_user(u_id):
    """Создание нового пользователя"""

    new_user = await Users.create(user_id=u_id, step="registration")
    await new_user.save()
    return new_user


async def check_user_in_db(u_id):
    """
    Проверка на наличие пользователя в базе
    Есть -- вернуть его
    Нет -- создать и вернуть
    """

    user = await get_user_row(u_id)
    new = False
    if not user:
        user = await create_new_user(u_id)
        new = True
    return user, new
