from datetime import datetime

from sqlalchemy import select, insert, update
from sqlalchemy.orm import joinedload

from database.db_config import async_session
from database.entities import User, Ad, AdCategory, Image, MessageId
from database.models import CreateAdRequest, AdResponse, CreateUserRequest


async def create_or_update_user(request: CreateUserRequest):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User)
                .where(User.telegram_id == request.telegram_id)
            )
            user = result.scalar_one_or_none()
            if user is None:
                await session.execute(insert(User), [{
                    'first_name': request.first_name,
                    'last_name': request.last_name,
                    'telegram_id': request.telegram_id,
                    'telegram_login': request.telegram_login
                }])
                return user
            else:
                user.last_login = datetime.now()
                return user


async def check_user_phone_is_none(user_telegram_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User)
                .where(User.telegram_id == user_telegram_id)
            )
            user = result.scalar_one()
            return user.phone is None


async def add_phone_to_user(phone, user_telegram_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(User)
                .where(User.telegram_id == user_telegram_id)
            )
            user = result.scalar_one()
            user.phone = phone


async def create_ad(request: CreateAdRequest):
    async with async_session() as session:
        async with session.begin():
            select_user_result = await session.execute(
                select(User)
                .where(User.telegram_id == request.user_id)
            )
            user = select_user_result.scalar_one()
            ad: Ad = await session.scalar(insert(Ad).returning(Ad), [{
                'user_id': user.id,
                'title': request.title,
                'description': request.description,
                'cost': int(request.cost),
                'category_id': request.category_id
            }])
            if request.media_id is not None:
                await session.execute(
                    update(Image)
                    .where(Image.media_id == request.media_id)
                    .values(ad_id=ad.id)
                )
            if request.file_id is not None:
                await session.execute(
                    update(Image)
                    .where(Image.image_id == request.file_id)
                    .values(ad_id=ad.id)
                )
            return AdResponse(
                ad_id=ad.id,
                title=ad.title,
                user_telegram=user.telegram_login,
                description=ad.description,
                cost=ad.cost,
                category=request.category_title,
                image_ids=[]
            )


async def fetch_category_by_alias(alias):
    async with async_session() as session:
        async with session.begin():
            select_category_result = await session.execute(
                select(AdCategory)
                .where(AdCategory.alias == alias)
            )
            category = select_category_result.scalar_one()
            return category


async def fetch_user_by_id(user_id):
    async with async_session() as session:
        async with session.begin():
            user_result = await session.execute(
                select(User)
                .where(User.telegram_id == user_id)
            )
            user = user_result.scalar_one()
            return user


async def fetch_ads_by_user(user_id):
    async with async_session() as session:
        async with session.begin():
            all_ads = []
            result = await session.execute(
                select(Ad)
                .where(User.telegram_id == user_id)
                .where(Ad.is_published)
            )
            ads_result = result.scalars().unique().all()
            count = 0
            for index, ad in enumerate(ads_result):
                ad_response = AdResponse(
                    ad.id,
                    ad.title,
                    ad.user.telegram_login,
                    ad.description,
                    ad.cost,
                    ad.category.title,
                    [image.image_id for image in ad.images]
                )
                all_ads.append(ad_response)
                count = index + 1
            return True if count > 0 else False, all_ads if count > 0 else 'Нет объявлений'


async def fetch_ads_to_validate():
    async with async_session() as session:
        async with session.begin():
            all_ads = []
            result = await session.execute(
                select(Ad)
                .where(Ad.is_valid.is_(False))
                .where(Ad.is_rejected.is_(False))
            )
            ads_result = result.scalars().unique().all()
            if ads_result:
                for ad in ads_result:
                    ad_response = AdResponse(
                        ad.id,
                        ad.title,
                        ad.user.telegram_login,
                        ad.description,
                        ad.cost,
                        ad.category.title,
                        [image.image_id for image in ad.images]
                    )
                    all_ads.append(ad_response)
            return all_ads


async def unpublished_ad(ad_id):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Ad)
                .options(joinedload(Ad.images))
                .where(Ad.id == int(ad_id))
            )
            ad = result.scalars().unique().all()
            first_ad = ad[0]
            first_ad.is_published = False
            await session.commit()
            return first_ad


async def reject_ad(ad_id):
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                update(Ad)
                .where(Ad.id == int(ad_id))
                .values(is_rejected=True)
            )


async def fetch_ad_by_id(ad_id: str):
    async with async_session() as session:
        async with session.begin():
            result = await session.execute(
                select(Ad)
                .where(Ad.id == int(ad_id))
            )
            ad = result.scalars().unique().all()
            return ad


async def set_publish_ad_id(ids):
    async with async_session() as session:
        async with session.begin():
            await session.execute(
                insert(MessageId), ids
            )
            await session.execute(
                update(Ad)
                .where(Ad.id == ids[0]['ad_id'])
                .values(is_published=True)
                .values(is_valid=True)
            )


async def save_photo_id_from_media_group(image_id: str, media_id=None):
    async with async_session() as session:
        async with session.begin():
            await session.scalar(insert(Image), [{
                'image_id': image_id or None,
                'media_id': media_id or None
            }])
