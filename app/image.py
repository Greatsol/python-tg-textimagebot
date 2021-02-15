from pathlib import Path

from PIL.Image import core as _imaging

from PIL import Image, ImageDraw, ImageFont

import env


async def put_text(
    text: str, img_path: Path, font_path: Path, font_color: str, name: int
):
    """Склеивает картинку и текст по заданным параметрам"""
    img = Image.open(img_path.absolute())

    img_width, img_height = img.size

    font_size = await find_font_size(img_height, img_width, text)
    font = ImageFont.truetype(str(font_path.absolute()), size=font_size)

    draw = ImageDraw.Draw(img)

    text_width, text_height = draw.textsize(text, font=font)

    draw.text(
        (int((img_width - text_width) / 2), int((img_height - text_height) / 2)),
        text,
        fill=font_color,
        font=font,
    )

    path = env.local_dir / env.TEMP_PATH
    path.mkdir(parents=True, exist_ok=True)
    file_path = path / f"{name}.png"

    img.save(file_path)
    return file_path


async def create_image(pic, text, name):
    """Удобная надстройка для put_text"""
    root_image = env.local_dir / env.IMAGE_PATH
    root_image.mkdir(parents=True, exist_ok=True)
    image_path = root_image / "imgs" / pic.category / pic.gender / pic.pic_path

    root_font = env.local_dir / env.FONT_PATH
    root_font.mkdir(parents=True, exist_ok=True)
    font_path = root_font / "fonts" / pic.font_path

    return await put_text(text, image_path, font_path, pic.font_color, name)


async def find_font_size(height, width, text):
    if height >= width:
        font_size = int(width / len(text))
    else:
        font_size = int(height / len(text))

    return font_size
