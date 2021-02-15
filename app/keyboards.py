from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)

from app import env
from app import strings as st


# Inline лавиатура с сылкой на группу
async def generate_join_group_kb(groups):
    join_group = InlineKeyboardMarkup()
    for group in groups:
        join_group.add(InlineKeyboardButton(group.description, url=f"t.me/{group.value}"))
    return join_group


async def generate_select_category(categories):
    select_category = InlineKeyboardMarkup()
    for category in categories:
        select_category.add(
            InlineKeyboardButton(category.category, callback_data=category.category)
        )
    return select_category


async def select_gender():
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(st.male, callback_data=st.male))
    keyboard.add(InlineKeyboardButton(st.female, callback_data=st.female))
    return keyboard


async def agree():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(st.yes))
    keyboard.add(KeyboardButton(st.no))
    return keyboard


async def create():
    keyboard = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True)
    keyboard.add(KeyboardButton(st.create))
    return keyboard


async def slider():
    keyboard = InlineKeyboardMarkup(row_width=2)
    inline_btn_1 = InlineKeyboardButton("◀️", callback_data="left")
    inline_btn_2 = InlineKeyboardButton("▶️", callback_data="right")
    inline_btn_3 = InlineKeyboardButton("Выбрать этот", callback_data="Выбрать")
    keyboard.add(inline_btn_1, inline_btn_2, inline_btn_3)
    return keyboard


async def create_link_btn(name, url):
    keyboard = InlineKeyboardMarkup()
    keyboard.add(InlineKeyboardButton(name, url=url))
    return keyboard
