if __name__ == "__main__":
    from app.utils import cli

    if cli.is_initialized:
        from app import bot



        bot.run_bot()
