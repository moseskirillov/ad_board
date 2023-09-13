import json
import logging
import re
import textwrap
import traceback
from pydoc import html

from telegram import Update, InputMediaPhoto, ReplyKeyboardRemove
from telegram.constants import ParseMode
from telegram.ext import ContextTypes

from bot.keyboards import start_keyboard, ad_keyboard, start_keyboard_admin, validate_keyboard
from database.models import CreateUserRequest
from database.services import create_or_update_user, add_phone_to_user, fetch_ads_by_user, unpublished_ad, \
    set_publish_ad_id, fetch_ads_to_validate, fetch_ad_by_id, reject_ad


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = await create_or_update_user(
        CreateUserRequest(
            first_name=update.effective_chat.first_name,
            last_name=update.effective_chat.last_name,
            telegram_id=update.effective_chat.id,
            telegram_login=update.effective_chat.username
        )
    )
    context.user_data['user_id'] = update.effective_chat.id
    if update.callback_query:
        await update.callback_query.answer()
    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=f'Привет, {update.effective_chat.first_name}! Выбери действие:',
        reply_markup=start_keyboard_admin if user and user.is_admin else start_keyboard
    )


async def view_ads_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id') or None
    if user_id:
        await update.callback_query.answer()
        status, ads_result = await fetch_ads_by_user(user_id)
        if status:
            for ad in ads_result:
                if len(ad.image_ids) > 1:
                    await context.bot.send_media_group(
                        chat_id=update.effective_chat.id,
                        media=[InputMediaPhoto(
                            media=file_id,
                            caption=ad.__str__() if index == 0 else None,
                            parse_mode=ParseMode.HTML
                        ) for index, file_id in enumerate(ad.image_ids)]
                    )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text='Выберите действие',
                        reply_markup=ad_keyboard(ad.ad_id),
                        parse_mode=ParseMode.HTML
                    )
                elif len(ad.image_ids) == 1:
                    await context.bot.send_photo(
                        photo=ad.image_ids[0],
                        chat_id=update.effective_chat.id,
                        caption=ad.__str__(),
                        reply_markup=ad_keyboard(ad.ad_id),
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=ad.__str__(),
                        reply_markup=ad_keyboard(ad.ad_id),
                        parse_mode=ParseMode.HTML
                    )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=ads_result
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Вы не залогинены. Для логина, сначала нажмите /start'
        )


async def delete_ad_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id') or None
    if user_id:
        await update.callback_query.answer()
        ad_id = re.findall(r'\d+', update.callback_query.data)[0]
        ad = await unpublished_ad(ad_id)
        for message in ad.messages:
            await context.bot.delete_message(
                chat_id='@wolrus_board',
                message_id=message.message_id
            )
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Объявление снято с публикации',
            reply_markup=start_keyboard
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Вы не залогинены. Для логина, сначала нажмите /start'
        )


async def add_phone_to_user_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id')
    if user_id:
        await add_phone_to_user(phone=update.message.contact.phone_number, user_telegram_id=update.message.chat_id)
        await update.message.reply_text(
            text='Теперь вы можете создать объявления',
            reply_markup=start_keyboard
        )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Вы не залогинены. Для логина, сначала нажмите /start'
        )


async def validate_ads_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id') or None
    if user_id:
        await update.callback_query.answer()
        ads_result = await fetch_ads_to_validate()
        if len(ads_result) > 0:
            for ad in ads_result:
                if len(ad.image_ids) > 1:
                    media = [InputMediaPhoto(
                        media=file_id,
                        caption=ad.__str__() if index == 0 else None,
                        parse_mode=ParseMode.HTML
                    ) for index, file_id in enumerate(ad.image_ids)]
                    await context.bot.send_media_group(
                        chat_id=update.effective_chat.id,
                        media=media
                    )
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        reply_markup=validate_keyboard(ad.ad_id),
                        text='Нажмите кнопку чтобы подтвердить или отклонить объявление'
                    )
                    context.chat_data['files'] = media
                elif len(ad.image_ids) == 1:
                    await context.bot.send_photo(
                        chat_id=update.effective_chat.id,
                        photo=ad.image_ids[0],
                        caption=ad.__str__(),
                        reply_markup=validate_keyboard(ad.ad_id),
                        parse_mode=ParseMode.HTML
                    )
                else:
                    await context.bot.send_message(
                        chat_id=update.effective_chat.id,
                        text=ad.__str__(),
                        reply_markup=validate_keyboard(ad.ad_id),
                        parse_mode=ParseMode.HTML
                    )
                context.bot_data['ad_user_id'] = ad.user_telegram
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Нет объявлений'
            )
    else:
        await update.callback_query.answer()
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Вы не залогинены. Для логина, сначала нажмите /start'
        )


async def validate_ad_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id') or None
    if user_id:
        await update.callback_query.answer()
        ad_id = re.findall(r'\d+', update.callback_query.data)[0]
        ads = await fetch_ad_by_id(ad_id=ad_id)
        if update.callback_query.data.startswith('approve'):
            for ad in ads:
                if len(ad.images) > 1:
                    results = await context.bot.send_media_group(
                        chat_id='@wolrus_board',
                        media=context.chat_data['files']
                    )
                    message_ids = [{'message_id': int(result.id), 'ad_id': int(ad_id)} for result in results]
                    await set_publish_ad_id(message_ids)
                elif len(ad.images) == 1:
                    result = await context.bot.send_photo(
                        chat_id='@wolrus_board',
                        photo=update.effective_message.photo[-1].file_id,
                        caption=update.effective_message.caption
                    )
                    await set_publish_ad_id([{'message_id': int(result.message_id), 'ad_id': int(ad_id)}])
                else:
                    result = await context.bot.send_message(
                        chat_id='@wolrus_board',
                        text=update.effective_message.text,
                        parse_mode=ParseMode.HTML
                    )
                    await set_publish_ad_id([{'message_id': int(result.message_id), 'ad_id': int(ad_id)}])
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text='Объявление опубликовано'
                )
                await context.bot.send_message(
                    chat_id=ad.user.telegram_id,
                    text=f'Ваше объявление опубликовано',
                    reply_markup=start_keyboard
                )
                context.bot_data['ad_user_id'] = ad.user.telegram_id
        else:
            ad = ads[0]
            await reject_ad(ad_id)
            context.bot_data['ad_user_id'] = ad.user.telegram_id
            context.chat_data['is_reject'] = True
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text='Напиши причину отклонения'
            )
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Вы не залогинены. Для логина, сначала нажмите /start'
        )


async def reject_ad_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = context.user_data.get('user_id') or None
    if user_id:
        if context.chat_data.get('is_reject'):
            reject_text = update.effective_message.text
            ad_user_id = context.bot_data['ad_user_id']
            await context.bot.send_message(
                chat_id=ad_user_id,
                text=f'Ваше объявление отклонено. Комментарий от модератора: {reject_text}',
                reply_markup=start_keyboard
            )
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Комментарий отправлен',
                reply_markup=start_keyboard
            )
        else:
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=f'Привет, {update.effective_chat.first_name}! Выбери действие:',
                reply_markup=start_keyboard
            )
        context.chat_data['is_reject'] = False
    else:
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text='Вы не залогинены. Для логина, сначала нажмите /start'
        )


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    logging.error('Произошла ошибка при работе бота:', exc_info=context.error)
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = ''.join(tb_list)
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    wrapped_traceback = textwrap.wrap(tb_string, width=2048)
    error_message = (
        f'<pre>Произошла ошибка при работе бота\n</pre>'
        f'<pre>update = {html.escape(json.dumps(update_str, indent=2, ensure_ascii=False))}'
        '</pre>\n\n'
        f'<pre>context.chat_data = {html.escape(str(context.chat_data))}</pre>\n\n'
        f'<pre>context.user_data = {html.escape(str(context.user_data))}</pre>\n\n'
    )
    await context.bot.send_message(chat_id='1472373299', text=error_message, parse_mode=ParseMode.HTML)

    for i, part in enumerate(wrapped_traceback):
        traceback_message = f'<pre>{html.escape(part)}</pre>'
        message = f'<pre>Стек-трейс, часть {i + 1} из ' \
                  f'{len(wrapped_traceback)}</pre>\n\n' \
                  f'{traceback_message}'
        await context.bot.send_message(chat_id='1472373299', text=message, parse_mode=ParseMode.HTML)

    await context.bot.send_message(
        chat_id=update.effective_chat.id,
        text='Произошла ошибка при работе бота. Пожалуйста, нажмите /start для новой попытки или попробуйте позже',
        parse_mode=ParseMode.HTML,
        reply_markup=ReplyKeyboardRemove()
    )
