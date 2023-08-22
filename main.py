import asyncio
import logging
import os

from telegram.ext import Application, ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters

from bot.ads_conversation import conversation_handler, conversation_publish
from bot.handlers import start_handler, view_ads_handler, add_phone_to_user_handler, validate_ad_handler, \
    reject_ad_handler, delete_ad_handler, validate_ads_handler
from bot.keyboards import view_ad_callback, validation_ad_callback, return_to_start_callback, publish_ad_callback
from database.db_config import database_init

token = os.getenv('BOT_TOKEN')

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)


def handlers_register(application: Application):
    application.add_handler(conversation_handler())
    application.add_handler(CommandHandler('start', start_handler))
    application.add_handler(CallbackQueryHandler(start_handler, pattern=return_to_start_callback))
    application.add_handler(CallbackQueryHandler(view_ads_handler, pattern=view_ad_callback))
    application.add_handler(CallbackQueryHandler(validate_ads_handler, pattern=validation_ad_callback))
    application.add_handler(CallbackQueryHandler(validate_ad_handler, pattern=r'approve_ad_\d+'))
    application.add_handler(CallbackQueryHandler(validate_ad_handler, pattern=r'disapprove_ad_\d+'))
    application.add_handler(CallbackQueryHandler(delete_ad_handler, pattern=r'delete_ad_\d+'))
    application.add_handler(CallbackQueryHandler(conversation_publish, pattern=publish_ad_callback))
    application.add_handler(MessageHandler(filters.TEXT, reject_ad_handler))
    application.add_handler(MessageHandler(filters.CONTACT, add_phone_to_user_handler))


def main():
    application = ApplicationBuilder().token(token).build()
    handlers_register(application)
    application.run_webhook(
        listen='0.0.0.0',
        port=int(os.getenv('PORT')),
        url_path=os.getenv('URL_PATH'),
        webhook_url=os.getenv('WEBHOOK_PATH'),
    )


if __name__ == '__main__':
    loop = asyncio.get_event_loop()
    loop.run_until_complete(database_init())
    main()
