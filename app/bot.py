import asyncio
import json
import logging
import os
import re
from pathlib import Path

from aiogram import Bot, Dispatcher, executor, types, utils

from app import env, image
from app import keyboards as kb
from app import strings as st
from app.db.db_functions import check_user_in_db, init_db
from app.models.category import Category
from app.models.mail import Mail
from app.models.pics import Pics
from app.models.promo import Promo
from app.models.settings import Settings
from app.models.users import Users

logging.basicConfig(level=logging.INFO)

loop = asyncio.get_event_loop()
bot = Bot(token=env.TELEGRAM_TOKEN)
dp = Dispatcher(bot)


async def download_file(file_id, local_path):
    file = await bot.get_file(file_id)
    download_to = env.local_dir / local_path

    download_to.mkdir(parents=True, exist_ok=True)
    await file.download(destination=download_to)
    return download_to / file.file_path


async def check_color(color):
    flag = True
    symbols = [
        "0",
        "1",
        "2",
        "3",
        "4",
        "5",
        "6",
        "7",
        "8",
        "9",
        "a",
        "b",
        "c",
        "d",
        "e",
        "f",
    ]
    for element in color[1:]:
        if element not in symbols:
            flag = False
    if len(color) != 7 or color[0] != "#":
        flag = False
    return flag


async def send_photo_with_path(path, user_id, reply_markup=None):
    with open(path, "rb") as data:
        return await bot.send_photo(user_id, data, reply_markup=reply_markup)


async def send_document_with_u_id(user_id, reply_markup=None):
    path = env.local_dir / env.TEMP_PATH
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{user_id}.png"

    with open(file_path, "rb") as data:
        try:
            return await bot.send_document(user_id, data, reply_markup=reply_markup)
        finally:
            os.remove(file_path)


async def check_groups_member(message, input_text=0):
    """Проверяет вступление в группы из env.py"""

    flag = False
    chat_id = message.from_user.id
    groups = await Settings.filter(name="channel").all()

    if not groups:
        await message.answer(st.groups_err)
        return 0

    for group in groups:
        try:
            if group.value.isdigit():
                is_member = await bot.get_chat_member(int(group.value), chat_id)
            else:
                is_member = await bot.get_chat_member("@" + group.value, chat_id)
        except utils.exceptions.BadRequest:
            await message.answer(st.not_group_admin + group.value)
        else:
            if is_member["status"] == "left":
                flag = False
            elif is_member["status"] == "kicked":
                await bot.send_message(chat_id, st.kicked)
                return False
            else:
                flag = True
    if flag:
        if input_text:
            await bot.send_message(
                chat_id, st.after_start, reply_markup=await kb.create()
            )
        return True
    else:
        await bot.send_message(
            chat_id, st.hello_string, reply_markup=await kb.generate_join_group_kb(groups)
        )


@dp.message_handler(commands=["start"])
async def send_welcome(message: types.Message):
    await check_groups_member(message, input_text=1)
    user, new = await check_user_in_db(message.chat.id)
    refer_id = ""
    promocode = None

    list_after_slpit = re.split(r"[ =]", message.text)
    if len(list_after_slpit) > 1:
        refer_id = list_after_slpit[1]
    if len(list_after_slpit) == 3 and new:
        promocode = list_after_slpit[2]
        promocode = await Promo.filter(name=promocode).first()
        if promocode:
            user.attempts = promocode.attempts
            user.promocode_ids = json.dumps([promocode.id])
            promocode.activate += 1
            await promocode.save()

    user.step = "0"
    await user.save()

    if new and refer_id != str(message.chat.id) and refer_id.isdigit():
        refer = await Users.filter(user_id=int(refer_id)).first()
        if refer:
            refer.attempts += env.ATTEMPTS_FOR_REFERAL
            refer.referals += 1
            await refer.save()
            await bot.send_message(refer.user_id, st.new_referal)


"""Admin commands"""


async def is_admin(msg):
    user = await Users.filter(user_id=msg.from_user.id).first()
    return user.role == "admin"


@dp.message_handler(is_admin, commands=["ahelp"])
async def help_for_admin(message: types.Message):
    await message.answer(st.admin_home)


async def check_to_send(message):
    admin = await Users.filter(user_id=message.chat.id).first()
    step = "send_to_all"
    return admin.step[:11] == step


async def send_to_users(text, name=None, url=None):
    users = await Users.all()

    if name and url:
        btn = await kb.create_link_btn(name, url)
        for user in users:
            await bot.send_message(user.user_id, text, reply_markup=btn)
    else:
        for user in users:
            await bot.send_message(user.user_id, text)


@dp.message_handler(is_admin, commands=["addadmin"])
async def add_admin(message: types.Message):
    try:
        u_id = int(message.text.split(" ")[1])
        user = await Users.filter(user_id=u_id).first()
        user.role = "admin"
        await user.save()
        await message.answer(st.new_admin)
        await bot.send_message(u_id, st.you_new_admin)
    except Exception:
        await message.answer(st.new_admin_err)


@dp.message_handler(is_admin, commands=["sendtoall"])
async def create_mail(message: types.Message):
    admin = await Users.filter(user_id=message.chat.id).first()
    admin.step = "send_to_all_text"
    await admin.save()
    await message.answer(st.input_text_for_mail)


@dp.message_handler(is_admin, check_to_send)
async def send_to_all(message: types.Message):
    admin = await Users.filter(user_id=message.chat.id).first()

    if message.text == st.exit:
        admin.step = "0"
        await admin.save()

    elif admin.step == "send_to_all_text":
        mail = await Mail.filter(user_id=message.chat.id).first()

        if not mail:
            mail = await Mail.create(user_id=message.chat.id, text=message.text)
        else:
            mail.text = message.text

        await mail.save()

        admin.step = "send_to_all_btn"
        await admin.save()

        await message.answer(st.use_mail_btn, reply_markup=await kb.agree())

    elif admin.step == "send_to_all_btn":
        mail = await Mail.filter(user_id=message.chat.id).first()

        if message.text == st.no:
            await send_to_users(mail.text)
            admin.step = "0"
            await admin.save()

            await message.answer(st.all_sent)
        else:
            admin.step = "send_to_all_url"
            await admin.save()

            await message.answer(st.input_btn_url)

    elif admin.step == "send_to_all_url":
        mail = await Mail.filter(user_id=message.chat.id).first()
        mail.url = message.text
        await mail.save()

        admin.step = "send_to_all_name"
        await admin.save()

        await message.answer(st.input_btn_name)

    elif admin.step == "send_to_all_name":
        mail = await Mail.filter(user_id=message.chat.id).first()

        await send_to_users(mail.text, message.text, mail.url)
        admin.step = "0"
        await admin.save()

        await message.answer(st.all_sent)


@dp.message_handler(is_admin, commands=["promolist"])
async def send_promo_list(message: types.Message):
    promocodes = await Promo.all()
    msg = "id\tname\tattempts\n"
    for promocode in promocodes:
        msg += f"{promocode.id} {promocode.name} {promocode.attempts}\n"
    await message.answer(msg)


# noinspection PyBroadException
@dp.message_handler(is_admin, commands=["addpromo"])
async def add_promo(message: types.Message):
    row = message.text.split(" ")
    try:
        old = await Promo.filter(name=row[1]).first()
        if not old:
            new_promocode = await Promo.create(name=row[1], attempts=int(row[2]))
            await new_promocode.save()
            link = f"t.me/{env.BOT_NAME}?start={message.chat.id}={new_promocode.name}"
            await message.answer(st.add_promo + link)
        else:
            await message.answer(st.add_promo_old)
    except Exception:
        await message.answer(st.add_promo_err)


# noinspection PyBroadException
@dp.message_handler(is_admin, commands=["removepromo"])
async def remove_promo(message: types.Message):
    row = message.text.split(" ")
    try:
        promocode = await Promo.filter(id=int(row[1])).first()
        await promocode.delete()
        await message.answer(st.remove_promo)
    except Exception:
        await message.answer(st.remove_promo_err)


@dp.message_handler(is_admin, commands=["statistics"])
async def create_statistic(message: types.Message):
    users = await Users.all().count()
    categories = await Category.all().count()
    pic = await Pics.all().count() - 1

    data = f"{st.user_statistics}{users}\n" \
           f"{st.category_statistics}{categories}" \
           f"\n{st.pics_statistics}{pic}"
    await message.answer(data)


@dp.message_handler(is_admin, commands=["add_infinity"])
async def give_inf(message: types.Message):
    user_id = message.text[14:]

    user = await Users.filter(user_id=user_id).first()
    user.attempts = 30000
    await user.save()
    await bot.send_message(user.user_id, st.inf)
    await message.answer(st.complete)


# noinspection PyBroadException
@dp.message_handler(is_admin, commands=["add"])
async def give(message: types.Message):
    try:
        args = message.text.split(" ")
        user_id = args[1]

        user = await Users.filter(user_id=user_id).first()
        user.attempts += int(args[2])
        await user.save()
        await bot.send_message(user.user_id, st.add + args[2])
        await message.answer(st.complete)
    except Exception:
        await message.answer(st.admin_home)


@dp.message_handler(is_admin, commands=["categorylist"])
async def show_categorylist(message: types.Message):
    categories = await Category.all()
    msg = ""

    if not categories:
        await message.answer(st.none_category)
        return 0

    for category in categories:
        msg += f"{category}\n"

    await message.answer(msg)


@dp.message_handler(is_admin, commands=["addcategory"])
async def add_category(message: types.Message):
    category_name = message.text[13:]
    if category_name == "":
        await message.answer(st.empty_category_name)
        return 0

    if await Category.filter(category=category_name).first():
        await message.answer(st.not_new_category)
    else:
        try:

            path = env.local_dir / "imgs" / category_name

            path.mkdir(parents=True)
            (path / st.male).mkdir()
            (path / st.female).mkdir()
            new_category = await Category.create(category=category_name)
            await new_category.save()
        except Exception as err:
            logging.error(err)
            await message.answer("Не удалось создать категорию")
            return
        await message.answer(st.create_category)


@dp.message_handler(is_admin, commands=["addpic"])
async def add_picture(message: types.Message):
    categories = await Category.all()
    if not categories:
        await message.answer(st.none_category)
        return 0

    keyboard = await kb.generate_select_category(categories)

    admin = await Users.filter(user_id=message.chat.id).first()
    admin.step = "select_category"
    await admin.save()

    await message.answer(st.select_category, reply_markup=keyboard)


async def check_step(message):
    admin = await Users.filter(user_id=message.from_user.id).first()
    steps = ["select_category", "select_gender", "add_img_path", "font_color", "agree"]
    if admin.step in steps:
        return 1
    else:
        return 0


@dp.callback_query_handler(is_admin, check_step)
async def select_callback_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    chat_id = callback_query.from_user.id
    data = callback_query.data
    admin = await Users.filter(user_id=chat_id).first()
    pic = await Pics.filter(id=1).first()

    if admin.step == "select_category":
        if pic:
            pic.category = data
        else:
            pic = await Pics.create(category=data)
        await pic.save()

        admin.step = "select_gender"
        await admin.save()

        await bot.send_message(
            chat_id, st.select_gender, reply_markup=await kb.select_gender()
        )

    elif admin.step == "select_gender" and data in [st.male, st.female]:
        pic.gender = data
        await pic.save()

        admin.step = "add_img_path"
        await admin.save()

        await bot.send_message(chat_id, st.input_img_path)


@dp.message_handler(is_admin, check_step)
async def add_pic(message: types.Message):
    admin = await Users.filter(user_id=message.chat.id).first()
    pic = await Pics.filter(id=1).first()

    if message.text == st.exit:
        admin.step = "0"
        await admin.save()

        await message.answer(st.admin_home)

    elif admin.step == "select_category":
        if pic:
            pic.category = message.text
        else:
            pic = await Pics.create(category=message.text)
        await pic.save()

        admin.step = "select_gender"
        await admin.save()

        await message.answer(st.select_gender, reply_markup=await kb.select_gender())

    elif admin.step == "select_gender":
        pic.gender = message.text
        await pic.save()

        admin.step = "add_img_path"
        await admin.save()

        await message.answer(st.input_img_path)

    elif admin.step == "font_color":
        color = message.text.lower()
        result = await check_color(color)

        if result:
            pic.font_color = color
            await pic.save()

            await message.answer(st.add_pic)

            path = await image.create_image(pic, st.test_text, admin.user_id)
            await send_photo_with_path(path, message.chat.id)

            admin.step = "agree"
            await admin.save()

            await message.answer(st.test_pic, reply_markup=await kb.agree())

        else:
            await message.answer(st.color_error)

    elif admin.step == "agree":
        if message.text == st.yes:
            new_pic = await Pics.create(
                category=pic.category,
                gender=pic.gender,
                pic_path=pic.pic_path,
                font_path=pic.font_path,
                font_color=pic.font_color,
                file_id=pic.file_id,
            )
            await new_pic.save()

            admin.step = "0"
            await admin.save()

            await message.answer(st.complete_adding)
        else:
            true_path = (
                    Path(env.local_dir) / "imgs" / pic.category / pic.gender / pic.pic_path
            )
            os.remove(true_path)

            admin.step = "0"
            await admin.save()

            await message.answer(st.cancel_pic)


@dp.message_handler(is_admin, content_types=["document"])
async def add_pic_and_font(message: types.Message):
    admin = await Users.filter(user_id=message.chat.id).first()
    pic = await Pics.filter(id=1).first()

    if admin.step == "add_img_path":
        root_image = env.local_dir / env.IMAGE_PATH

        root_image.mkdir(exist_ok=True, parents=True)
        local_path = root_image / pic.category / pic.gender
        pic_path = await download_file(message.document.file_id, local_path)
        pic.pic_path = pic_path
        pic.file_id = message.document.file_id
        await pic.save()

        admin.step = "add_font_path"
        await admin.save()

        await message.answer(st.input_font_path)

    elif admin.step == "add_font_path":
        name = message.document.file_name
        if name[-4:] == ".ttf":
            root_image = env.local_dir / env.FONT_PATH

            root_image.mkdir(exist_ok=True, parents=True)
            file_name = await download_file(message.document.file_id, root_image)

            pic.font_path = file_name
            await pic.save()

            admin.step = "font_color"
            await admin.save()

            await message.answer(st.input_font_color)
        else:
            await message.answer(st.input_font_path)


"""Логика для пользователя"""


@dp.message_handler(check_groups_member, commands=["info"])
async def send_help(message: types.Message):
    user = await Users.filter(user_id=message.chat.id).first()
    user.step = "0"
    await user.save()

    await message.answer(st.help_message, reply_markup=await kb.create())


@dp.message_handler(check_groups_member, commands=["help"])
async def send_info(message: types.Message):
    user = await Users.filter(user_id=message.chat.id).first()
    user.step = "0"
    await user.save()

    info = f"{st.attempts}{user.attempts}\n" \
           f"{st.referals}{user.referals}\n\n" \
           f"{st.referal_url}t.me/{env.BOT_NAME}?start={user.user_id}\n" \
           f"{st.buy_attempts}{env.ADMIN}"
    await message.answer(info, reply_markup=await kb.create())


# noinspection PyBroadException
@dp.message_handler(check_groups_member, commands=["promo"])
async def use_promo(message: types.Message):
    row = message.text.split(" ")
    try:
        promocode = await Promo.filter(name=row[1]).first()
        if promocode:
            user = await Users.filter(user_id=message.chat.id).first()
            exclude_id = json.loads(user.promocode_ids)
            if promocode.id not in exclude_id:
                exclude_id.append(promocode.id)
                user.promocode_ids = json.dumps(exclude_id)
                user.attempts += promocode.attempts
                await user.save()
                promocode.activate += 1
                await promocode.save()
                await message.answer(st.use_promo + str(promocode.attempts))
            else:
                await message.answer(st.use_promo_old)
        else:
            await message.answer(st.use_promo_not_found)
    except Exception:
        await message.answer(st.use_promo_err)


@dp.message_handler(check_groups_member)
async def create_user_pic(message: types.Message):
    user = await Users.filter(user_id=message.chat.id).first()
    info = f"{st.attempts}{user.attempts}\n" \
           f"{st.referals}{user.referals}\n\n" \
           f"{st.referal_url}t.me/{env.BOT_NAME}?{user.user_id}\n\n" \
           f"{st.buy_attempts}{env.ADMIN}"

    if message.text == st.exit:
        user.step = "0"
        await user.save()
        await message.answer(info, reply_markup=await kb.create())

    elif user.step in ["registration", "0"] and message.text.lower() == st.create.lower():
        if user.attempts >= 1:
            categories = await Category.all()

            keyboard = await kb.generate_select_category(categories)

            user.step = "u_select_category"
            await user.save()

            await message.answer(st.user_select_category, reply_markup=keyboard)
        else:
            no_attempts = f"{st.no_attempts}\n" \
                          f"{st.referal_url}t.me/{env.BOT_NAME}?{user.user_id}\n" \
                          f"{st.buy_attempts}{env.ADMIN}"
            await message.answer(no_attempts)

    elif user.step == "u_input_text":
        if len(message.text) > 30:
            await message.answer(st.out_of_range)
        else:
            wait_msg = await bot.send_message(user.user_id, st.wait)
            pic = await Pics.filter(category=user.category, gender=user.gender).exclude(id=1).first()

            path = await image.create_image(pic, message.text, user.user_id)
            msg = await send_photo_with_path(
                path, message.chat.id, reply_markup=await kb.slider()
            )
            await bot.delete_message(user.user_id, wait_msg.message_id)

            user.text = message.text
            user.pic_id = pic.id
            user.message_id = msg.message_id
            await user.save()


async def get_next_pic(category, gender, current_id, reverse=False):
    pics = await Pics.filter(category=category, gender=gender).exclude(id=1).all()

    pics_ids = list(map(lambda pic: pic.id, pics))
    del pics

    index = pics_ids.index(current_id)
    if not reverse:
        if index + 1 == len(pics_ids):
            next_id = pics_ids[0]
        else:
            next_id = pics_ids[index + 1]
    else:
        if index == 0:
            next_id = pics_ids[-1]
        else:
            next_id = pics_ids[index - 1]

    return await Pics.filter(id=next_id).first()


async def flip_image(callback_query, reverse=False):
    await bot.answer_callback_query(callback_query.id)

    user = await Users.filter(user_id=callback_query.from_user.id).first()

    if user.step == "u_input_text":
        wait_msg = await bot.send_message(user.user_id, st.wait)
        pic = await get_next_pic(
            user.category, user.gender, user.pic_id, reverse=reverse
        )

        path = await image.create_image(pic, user.text, user.user_id)
        msg = await send_photo_with_path(path, user.user_id, kb=await kb.slider())
        await bot.delete_message(user.user_id, wait_msg.message_id)
        await bot.delete_message(user.user_id, user.message_id)

        user.pic_id = pic.id
        user.message_id = msg.message_id
        await user.save()


@dp.callback_query_handler(text="right")
async def process_right_callback_button(callback_query: types.CallbackQuery):
    await flip_image(callback_query)


@dp.callback_query_handler(text="left")
async def process_left_callback_button(callback_query: types.CallbackQuery):
    await flip_image(callback_query, reverse=True)


@dp.callback_query_handler(text="Выбрать")
async def process_select_callback_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    user = await Users.filter(user_id=callback_query.from_user.id).first()

    if user.step == "u_input_text":
        msg = await bot.send_message(user.user_id, st.wait)
        await send_document_with_u_id(user.user_id)
        await bot.delete_message(user.user_id, msg.message_id)

        user.step = "0"
        user.attempts -= 1
        await user.save()

        info = f"""
{st.attempts}{user.attempts}
{st.referals}{user.referals}\n
{st.referal_url}t.me/{env.BOT_NAME}?start={user.user_id}\n
{st.buy_attempts}{env.ADMIN}
    """
        await bot.send_message(user.user_id, info, reply_markup=await kb.create())


@dp.callback_query_handler(check_groups_member)
async def process_callback_button(callback_query: types.CallbackQuery):
    await bot.answer_callback_query(callback_query.id)

    chat_id = callback_query.from_user.id
    data = callback_query.data

    user = await Users.filter(user_id=chat_id).first()

    if user.step == "u_select_category":
        categories = await Category.all()
        categories_names = map(lambda category: category.category, categories)
        if data in categories_names:
            user.category = data
            user.step = "u_select_gender"
            await user.save()

            await bot.send_message(
                chat_id, st.select_gender, reply_markup=await kb.select_gender()
            )

    elif user.step == "u_select_gender":
        if data != st.male and data != st.female:
            await bot.send_message(chat_id, st.use_keys)
        else:
            user.gender = data
            user.step = "u_input_text"
            await user.save()

            await bot.send_message(chat_id, st.user_input_text)


def run_bot():
    """
    todo: переделать бы нормально
    """

    loop.run_until_complete(init_db())
    executor.start_polling(dp, skip_updates=True)
