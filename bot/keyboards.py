from telegram import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)

create_ad_callback = "create_ad"
return_to_start_callback = "return_to_start_callback"
conversation_skip_image_callback = "conversation_skip_image_callback"
view_ad_callback = "view_ad"
validation_ad_callback = "validation_ad"
cancel_callback = "cancel_callback"
send_ad_title_callback = "send_ad_title_callback"
send_ad_description_callback = "send_ad_description_callback"
publish_ad_callback = "publish_ad_callback"
approve_ad_callback = "approve_ad_callback"
disapprove_ad_callback = "disapprove_ad_callback"
home_category_callback = "home_category_callback"
work_category_callback = "work_category_callback"
goods_category_callback = "goods_category_callback"
services_category_callback = "services_category_callback"
send_contact_text = "Отправить контакт"
publish_ad_text = "Опубликовать"

start_keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text="Создать объявление", callback_data=create_ad_callback
            )
        ],
        [InlineKeyboardButton(text="Мои объявления", callback_data=view_ad_callback)],
    ]
)

return_to_start_keyboard = InlineKeyboardMarkup(
    [[InlineKeyboardButton(text="Отменить", callback_data=return_to_start_callback)]]
)

conversation_skip_image_keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text="Пропустить", callback_data=conversation_skip_image_callback
            )
        ],
        [InlineKeyboardButton(text="Отменить", callback_data=return_to_start_callback)],
    ]
)

start_keyboard_admin = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(
                text="Создать объявление", callback_data=create_ad_callback
            )
        ],
        [InlineKeyboardButton(text="Мои объявления", callback_data=view_ad_callback)],
        [InlineKeyboardButton(text="Валидация", callback_data=validation_ad_callback)],
    ]
)

publish_ad_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton(text=publish_ad_text, callback_data=publish_ad_callback)],
        [InlineKeyboardButton(text="Отменить", callback_data=return_to_start_callback)],
    ]
)

send_contact_keyboard = ReplyKeyboardMarkup(
    [[KeyboardButton(text=send_contact_text, request_contact=True)]],
    resize_keyboard=True,
    one_time_keyboard=True,
)

category_ad_keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton(text="Жилье", callback_data=home_category_callback),
            InlineKeyboardButton(text="Работа", callback_data=work_category_callback),
        ],
        [
            InlineKeyboardButton(text="Товары", callback_data=goods_category_callback),
            InlineKeyboardButton(
                text="Услуги", callback_data=services_category_callback
            ),
        ],
        [InlineKeyboardButton(text="Отменить", callback_data=return_to_start_callback)],
    ]
)


def create_contact_keyboard(seller_contact):
    return InlineKeyboardMarkup(
        [[InlineKeyboardButton(text="Написать продавцу", url=seller_contact)]]
    )


def ad_keyboard(ad_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text="Снять с публикации", callback_data=f"delete_ad_{ad_id}"
                )
            ],
            [
                InlineKeyboardButton(
                    text="Назад", callback_data=return_to_start_callback
                )
            ],
        ]
    )


def validate_keyboard(ad_id):
    return InlineKeyboardMarkup(
        [
            [
                InlineKeyboardButton(
                    text=publish_ad_text, callback_data=f"approve_ad_{ad_id}"
                ),
                InlineKeyboardButton(
                    text="Отклонить", callback_data=f"disapprove_ad_{ad_id}"
                ),
            ],
            [
                InlineKeyboardButton(
                    text="Назад", callback_data=return_to_start_callback
                )
            ],
        ]
    )
