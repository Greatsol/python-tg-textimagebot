PROJECT := aiogram_bot
LOCALES_DOMAIN := bot
LOCALES_DIR := res/i18n
VERSION := 0.1

isort:
	isort app/

black:
	black app/

flake8:
	flake8 app/

lint: isort black flake8

gettext:
	echo "gettext"

updatetext:
	echo "updatetext"

compiletext:
	echo "compiletext"

update:
	echo "sorry my friend!"

build:
	echo "sorry, we don't have locales"

get-requirements:
	poetry export --dev -f requirements.txt -o requirements.txt

run:
	poetry run python -m app
