from logging.config import fileConfig
import os
from sqlalchemy import engine_from_config, pool
from alembic import context
from dotenv import load_dotenv

# Загрузка переменных окружения из .env файла
load_dotenv()

# Установка конфигурации Alembic
config = context.config

# Настройка логирования из .ini файла, если указан
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Получаем значение DATABASE_URL из переменных окружения
database_url = os.getenv('DATABASE_URL', 'sqlite:///./test.db')

# Проверка значения DATABASE_URL
if not database_url:
    raise ValueError("DATABASE_URL is not set or is empty")

# Устанавливаем URL для подключения к базе данных
config.set_main_option('sqlalchemy.url', str(database_url))

# Импортируем модели для поддержки autogenerate
from biznes_vokrug_backend.models import Base

# Метаданные для Alembic
target_metadata = [Base.metadata]

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata
        )
        with context.begin_transaction():
            context.run_migrations()

# Определяем режим работы и запускаем миграции
if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
