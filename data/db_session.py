from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import sqlalchemy.ext.declarative as dec

SqlAlchemyBase = dec.declarative_base()

__factory = None


async def global_init(db_file):
    global __factory

    if __factory:
        return

    if not db_file or not db_file.strip():
        raise Exception("Необходимо указать файл базы данных.")

    conn_str = f'sqlite+aiosqlite:///{db_file.strip()}?check_same_thread=False'

    engine = create_async_engine(conn_str, echo=False)
    __factory = sessionmaker(bind=engine, class_=AsyncSession)

    from . import __all_models

    async with engine.begin() as conn:
        await conn.run_sync(SqlAlchemyBase.metadata.create_all)


async def create_session() -> AsyncSession:
    global __factory
    return __factory()
