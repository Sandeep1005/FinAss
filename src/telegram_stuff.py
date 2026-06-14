import logging
from pathlib import Path

from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    ContextTypes,
    MessageHandler,
    filters,
)

from sqlite_stuff import DatabaseHandler


class TelegramBot:
    def __init__(
        self, 
        bot_token, 
        my_user_id,
        download_dir
    ):

        self.bot_token = bot_token
        self.my_user_id = my_user_id
        self.download_dir = Path(download_dir)

        # Create the dir if not exists
        self.download_dir.mkdir(exist_ok=True)

        logging.basicConfig(
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            level=logging.INFO,
        )
        self.logger = logging.getLogger(__name__)

    async def save_file(self, tg_file, filename: str):
        """
        Download a Telegram file to the downloads directory.
        """
        filepath = self.download_dir / filename
        await tg_file.download_to_drive(custom_path=str(filepath))
        self.logger.info("Saved attachment: %s", filepath)
        return filepath

    async def process_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle all incoming messages.
        """

        # DB handler
        db = context.bot_data["db"]

        # Check if there is a user
        if update.effective_user is None:
            return

        user_id = update.effective_user.id

        # Ignore everyone except yourself
        if user_id != self.my_user_id:
            self.logger.info(
                "Ignoring message from %s (%s)",
                update.effective_user.username,
                user_id,
            )
            return

        msg = update.effective_message

        print("=" * 80)
        if msg:
            if msg.from_user:
                print(f"From       : {msg.from_user.full_name}")
                print(f"User ID    : {msg.from_user.id}")
            print(f"Chat ID    : {msg.chat_id}")
            print(f"Message ID : {msg.message_id}")
            print(f"Date       : {msg.date}")

            if msg.text:
                print(f"Text        : {msg.text}")

            if msg.caption:
                print(f"Caption     : {msg.caption}")

            # --------------------------------------------------------
            # Photos
            # --------------------------------------------------------
            if msg.photo:
                photo = msg.photo[-1]  # Highest resolution
                file = await context.bot.get_file(photo.file_id)
                filepath = await self.save_file(file, f"photo_{photo.file_unique_id}.jpg")
                await msg.reply_text("✅ Photo received successfully.")

                # Inserting into db
                db.soft_delete_entry(message_id=msg.message_id)
                db.insert_entry(
                    message_id=msg.message_id,
                    date=msg.date,
                    has_media=True,
                    text=msg.caption,
                    media_url=str(filepath)
                )

            # --------------------------------------------------------
            # Documents (PDFs, ZIPs, etc.)
            # --------------------------------------------------------
            elif msg.document:
                if msg.document.mime_type == "application/pdf":
                    doc = msg.document
                    file = await context.bot.get_file(doc.file_id)

                    filename = doc.file_name or f"document_{doc.file_unique_id}"
                    filepath = await self.save_file(file, filename)
                    await msg.reply_text("✅ PDF received successfully.")

                    # Inserting into db
                    db.soft_delete_entry(message_id=msg.message_id)
                    db.insert_entry(
                        message_id=msg.message_id,
                        date=msg.date,
                        has_media=True,
                        text=msg.caption,
                        media_url=str(filepath)
                    )
                else:
                    await msg.reply_text(
                        "❌ This file format is not supported.\n"
                        "Please send either a photo or a PDF document."
                    )
                    return

            # Any other attachment type (video, audio, sticker, etc.)
            elif any([
                msg.video,
                msg.audio,
                msg.voice,
                msg.video_note,
                msg.sticker,
                msg.animation,
            ]):
                await msg.reply_text(
                    "❌ This file format is not supported.\n"
                    "Please send either a photo or a PDF document."
                )
                return

            elif msg.text:
                # Just a text message
                # Inserting into db
                db.soft_delete_entry(message_id=msg.message_id)
                db.insert_entry(
                    message_id=msg.message_id,
                    date=msg.date,
                    has_media=False,
                    text=msg.text
                )

            print("=" * 80)
    
    def run_bot(self, db_handler: DatabaseHandler):
        app = (
            ApplicationBuilder()
            .token(self.bot_token)
            .build()
        )

        # DB
        app.bot_data["db"] = db_handler

        # Listen for every kind of message update
        app.add_handler(
            MessageHandler(
                filters.ALL,
                self.process_message,
            )
        )

        print("Telegram bot listener started...")
        app.run_polling(
            allowed_updates=Update.ALL_TYPES,
            drop_pending_updates=False,
        )
