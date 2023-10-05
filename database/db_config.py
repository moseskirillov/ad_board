import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from database.entities import Base

engine = create_async_engine(os.getenv("DB_CONNECTION_STRING"), echo=True)
async_session = async_sessionmaker(engine, expire_on_commit=False)


async def database_init():
    async with engine.begin() as connection:
        await connection.run_sync(Base.metadata.create_all)
