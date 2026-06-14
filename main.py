from telegram_stuff import TelegramBot
from sqlite_stuff import DatabaseHandler

from dotenv import load_dotenv
import os


def main():
    print("Hello from finass!")

    ## Initializing 
    # Env variables
    load_dotenv()

    # Database
    db_handler = DatabaseHandler(db_path='db/sqlite.db')
    db_handler.initialize_database()

    # Telegram stuff
    bot = TelegramBot(
        bot_token=os.getenv("BOT_TOKEN", "bot_token"),
        my_user_id=int(os.getenv("MY_USER_ID", 0000)),
        download_dir="downloads"
    )

    ## Starting bot
    bot.run_bot(db_handler=db_handler)
    

if __name__ == "__main__":
    main()
