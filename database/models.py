from dataclasses import dataclass


@dataclass
class CreateUserRequest:
    first_name: str
    last_name: str
    telegram_id: int
    telegram_login: str


@dataclass
class CreateAdRequest:
    user_id: str
    title: str
    description: str
    file_id: str
    message_id: str
    cost: int
    category_title: str
    category_id: int
    media_id: int


@dataclass
class AdResponse:
    ad_id: str
    title: str
    user_telegram: str
    description: str
    cost: int
    category: str
    image_ids: [str]

    def __str__(self) -> str:
        return (
            f"<b>{self.title}</b>\n\n"
            f"<b>Описание:</b>\n{self.description}\n\n"
            f"<b>Цена:</b> {self.cost} руб.\n\n"
            f"<b>Категория:</b> #{self.category}\n"
            f"<b>Продавец:</b> @{self.user_telegram}"
        )
