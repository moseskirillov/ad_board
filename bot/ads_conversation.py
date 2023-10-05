from telegram import Update, InputMediaPhoto
from telegram.constants import ParseMode
from telegram.ext import (
    ConversationHandler,
    ContextTypes,
    CallbackQueryHandler,
    MessageHandler,
    filters,
)

from bot.keyboards import (
    create_ad_callback,
    send_contact_keyboard,
    category_ad_keyboard,
    home_category_callback,
    work_category_callback,
    goods_category_callback,
    services_category_callback,
    validate_keyboard,
    start_keyboard,
    return_to_start_callback,
    return_to_start_keyboard,
    start_keyboard_admin,
    conversation_skip_image_callback,
    conversation_skip_image_keyboard,
    publish_ad_keyboard,
)
from database.models import CreateAdRequest
from database.services import (
    check_user_phone_is_none,
    create_ad,
    fetch_all_admins,
    fetch_category_by_alias,
    fetch_user_by_id,
    save_photo_id_from_media_group,
)

TITLE, DESCRIPTION, COST, CATEGORY, IMAGE, SEND = range(6)


def conversation_handler():
    return ConversationHandler(
        entry_points=[
            CallbackQueryHandler(conversation_start, pattern=create_ad_callback)
        ],
        states={
            TITLE: [
                MessageHandler(filters.TEXT & ~filters.COMMAND, conversation_title)
            ],
            DESCRIPTION: [
                MessageHandler(
                    filters.TEXT & ~filters.COMMAND, conversation_description
                )
            ],
            COST: [MessageHandler(filters.TEXT & ~filters.COMMAND, conversation_cost)],
            CATEGORY: [
                CallbackQueryHandler(
                    conversation_category, pattern=home_category_callback
                ),
                CallbackQueryHandler(
                    conversation_category, pattern=work_category_callback
                ),
                CallbackQueryHandler(
                    conversation_category, pattern=goods_category_callback
                ),
                CallbackQueryHandler(
                    conversation_category, pattern=services_category_callback
                ),
            ],
            IMAGE: [
                MessageHandler(filters.PHOTO, conversation_image),
                CallbackQueryHandler(
                    conversation_image, pattern=conversation_skip_image_callback
                ),
            ],
            SEND: [
                MessageHandler(filters.PHOTO, conversation_publish),
            ],
        },
        fallbacks=[
            CallbackQueryHandler(conversation_cancel, pattern=return_to_start_callback)
        ],
        allow_reentry=True,
    )


async def conversation_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    await update.callback_query.answer()
    if user_id:
        phone_is_none = await check_user_phone_is_none(update.effective_chat.id)
        if phone_is_none:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Чтобы добавить объявление, нужно указать телефон. "
                "Пожалуйста, нажмите на кнопку «Отправить контакт».",
                reply_markup=send_contact_keyboard,
            )
        elif update.effective_user.username is None:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Чтобы добавить объявление, нужно указать username. "
                "Это нужно, чтобы указать ссылку на ваш Telegram в объявлении. "
                "Пожалуйста, добавьте его и попробуйте еще раз.",
                reply_markup=start_keyboard,
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text="Напишите заголовок",
                reply_markup=return_to_start_keyboard,
            )
            return TITLE
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не залогинены. Для логина, сначала нажмите /start",
        )


async def conversation_title(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if user_id:
        title = update.message.text
        context.user_data["title"] = title
        await update.message.reply_text(
            text=f"<b>Заголовок:</b> {title}\n\n"
            f"Теперь напишите описание для объявления",
            reply_markup=return_to_start_keyboard,
            parse_mode=ParseMode.HTML,
        )
        return DESCRIPTION
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не залогинены. Для логина, сначала нажмите /start",
        )


async def conversation_description(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if user_id:
        title = context.user_data["title"]
        description = update.message.text
        context.user_data["description"] = description
        await update.message.reply_text(
            text=f"<b>Заголовок:</b> {title}\n\n"
            f"<b>Описание:</b> {description}\n\n"
            f"Теперь напишите стоимость в рублях",
            reply_markup=return_to_start_keyboard,
            parse_mode=ParseMode.HTML,
        )
        return COST
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не залогинены. Для логина, сначала нажмите /start",
        )


async def conversation_cost(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if user_id:
        title = context.user_data["title"]
        description = context.user_data["description"]
        cost = update.message.text
        try:
            cost = int(cost)
        except ValueError:
            await update.message.reply_text(
                text="Сумма должна быть написана только цифрами без пробелов и букв.\n"
                "Пожалуйста внесите корректное значение"
            )
            return COST
        context.user_data["cost"] = cost
        await update.message.reply_text(
            text=f"<b>Заголовок:</b> {title}\n\n"
            f"<b>Описание:</b> {description}\n\n"
            f"<b>Стоимость:</b> <b>{cost} руб.</b>\n\n"
            f"Теперь выберите категорию",
            reply_markup=category_ad_keyboard,
            parse_mode=ParseMode.HTML,
        )
        return CATEGORY
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не залогинены. Для логина, сначала нажмите /start",
        )


async def conversation_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if user_id:
        await update.callback_query.answer()
        title = context.user_data["title"]
        description = context.user_data["description"]
        cost = context.user_data["cost"]
        category_alias = update.callback_query.data
        category = await fetch_category_by_alias(category_alias)
        context.user_data["category"] = category
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"<b>Заголовок:</b> {title}\n\n"
            f"<b>Описание:</b> {description}\n\n"
            f"<b>Стоимость:</b> <b>{cost} руб.</b>\n\n"
            f"<b>Категория:</b> <b>{category.title}</b>\n\n"
            f"Теперь пришлите фотографии, не более 5 штук",
            parse_mode=ParseMode.HTML,
            reply_markup=conversation_skip_image_keyboard,
        )
        return IMAGE
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не залогинены. Для логина, сначала нажмите /start",
        )


async def conversation_image(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if user_id:
        if update.callback_query:
            await update.callback_query.answer()
        message = update.effective_message
        if message.media_group_id:
            jobs = context.job_queue.get_jobs_by_name("images_media_group_sender")
            file_id = message.photo[-1].file_id
            if jobs:
                jobs[0].data["files"].append(file_id)
            else:
                context.job_queue.run_once(
                    callback=process_images_handler,
                    when=1,
                    data={
                        "files": [file_id],
                        "media_id": message.media_group_id,
                        "caption": {
                            "title": context.user_data["title"],
                            "description": context.user_data["description"],
                            "cost": context.user_data["cost"],
                            "category": context.user_data["category"],
                        },
                    },
                    name="images_media_group_sender",
                    chat_id=update.effective_chat.id,
                )
            await save_photo_id_from_media_group(file_id, message.media_group_id)
            return IMAGE
        else:
            if update.callback_query:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="Нажмите кнопку для публикации",
                    reply_markup=publish_ad_keyboard,
                )
            else:
                file_id = message.photo[-1].file_id
                title = context.user_data["title"]
                description = context.user_data["description"]
                cost = context.user_data["cost"]
                category = context.user_data["category"]
                context.chat_data["photo_id"] = file_id
                await save_photo_id_from_media_group(file_id)
                await context.bot.send_photo(
                    chat_id=update.effective_chat.id,
                    photo=file_id,
                    caption=f"<b>Заголовок:</b> {title}\n\n"
                    f"<b>Описание:</b> {description}\n\n"
                    f"<b>Стоимость:</b> <b>{cost} руб.</b>\n\n"
                    f"<b>Категория:</b> <b>{category.title}</b>\n\n"
                    f"Нажмите кнопку для публикации",
                    parse_mode=ParseMode.HTML,
                    reply_markup=publish_ad_keyboard,
                )
            return SEND
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не залогинены. Для логина, сначала нажмите /start",
        )


async def process_images_handler(context: ContextTypes.DEFAULT_TYPE):
    caption = context.job.data["caption"]
    caption_text = (
        f'<b>Заголовок:</b> {caption["title"]}\n\n'
        f'<b>Описание:</b> {caption["description"]}\n\n'
        f'<b>Стоимость:</b> {caption["cost"]} руб.\n\n'
        f'<b>Категория:</b> {caption["category"].title}\n\n'
    )
    files = [
        InputMediaPhoto(
            media=file_id,
            caption=caption_text if index == 0 else None,
            parse_mode=ParseMode.HTML,
        )
        for index, file_id in enumerate(context.job.data["files"])
    ]
    context.chat_data["files"] = files
    if len(files) > 5:
        await context.bot.send_message(
            chat_id=context.job.chat_id, text="Максимальное количество фото - 5 штук"
        )
    else:
        await context.bot.send_media_group(
            chat_id=context.job.chat_id,
            media=files,
        )
        await context.bot.send_message(
            chat_id=context.job.chat_id,
            text="Для публикации нажмите на кнопку",
            reply_markup=publish_ad_keyboard,
        )
        context.chat_data["media_id"] = context.job.data["media_id"]
    return ConversationHandler.END


async def conversation_publish(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if user_id:
        await update.callback_query.answer()
        title = context.user_data["title"]
        description = context.user_data["description"]
        cost = context.user_data["cost"]
        category = context.user_data["category"]
        file_id = context.chat_data.get("photo_id") or None
        media_id = context.chat_data.get("media_id") or None
        create_ad_response = await create_ad(
            CreateAdRequest(
                user_id=user_id,
                title=title,
                description=description,
                file_id=file_id,
                message_id="",
                cost=cost,
                category_title=category.title,
                category_id=category.id,
                media_id=media_id,
            )
        )
        users = await fetch_all_admins()
        for user in users:
            if file_id:
                await context.bot.send_photo(
                    chat_id=user.telegram_id,
                    photo=file_id,
                    caption=f"{create_ad_response.__str__()}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=validate_keyboard(create_ad_response.ad_id),
                )
            elif media_id:
                files = [
                    InputMediaPhoto(
                        media=file.media,
                        caption=create_ad_response.__str__() if index == 0 else None,
                        parse_mode=ParseMode.HTML,
                    )
                    for index, file in enumerate(context.chat_data["files"])
                ]
                context.chat_data["files"] = files
                await context.bot.send_media_group(
                    chat_id=user.telegram_id, media=files
                )
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text="Подтвердите или отклоните объявление",
                    parse_mode=ParseMode.HTML,
                    reply_markup=validate_keyboard(create_ad_response.ad_id),
                )
            else:
                await context.bot.send_message(
                    chat_id=user.telegram_id,
                    text=f"{create_ad_response.__str__()}",
                    parse_mode=ParseMode.HTML,
                    reply_markup=validate_keyboard(create_ad_response.ad_id),
                )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Ваше объявление принято и после модерации будет "
            "опубликовано в канале.\n"
            "Нажмите /start для возврата в главное меню",
            parse_mode=ParseMode.HTML,
        )
        context.chat_data["photo_id"] = None
        context.chat_data["media_id"] = None
        return ConversationHandler.END
    else:
        await update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не залогинены. Для логина, сначала нажмите /start",
        )


async def conversation_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get("user_id")
    if user_id:
        user = await fetch_user_by_id(user_id)
        await update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"Привет, {update.effective_chat.first_name}! Выбери действие:",
            reply_markup=start_keyboard_admin if user.is_admin else start_keyboard,
            parse_mode=ParseMode.HTML,
        )
        return ConversationHandler.END
    else:
        await update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы не залогинены. Для логина, сначала нажмите /start",
        )
