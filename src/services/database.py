"""
Модуль для работы с базой данных PostgreSQL.
Использует SQLAlchemy для ORM и asyncpg для асинхронной работы с PostgreSQL.
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy import String, Integer, DateTime, BigInteger, Text
from datetime import datetime
from typing import Optional, List
import logging
from .config import config

# База для моделей
class Base(DeclarativeBase):
    pass

# Модель для хранения истории сообщений
class ChatMessage(Base):
    __tablename__ = "chat_messages"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    message_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    text: Mapped[str] = mapped_column(Text)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<ChatMessage(chat_id={self.chat_id}, message_id={self.message_id}, username={self.username})>"

# Модель для хранения метрик генерации мемов
class MemeGenerationLog(Base):
    __tablename__ = "meme_generation_logs"
    
    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    chat_id: Mapped[int] = mapped_column(BigInteger, index=True)
    user_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    trigger_emoji: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)
    search_query: Mapped[str] = mapped_column(String(500))
    success: Mapped[bool] = mapped_column(default=True)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    generation_time: Mapped[Optional[float]] = mapped_column(nullable=True)  # в секундах
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, index=True)
    
    def __repr__(self):
        return f"<MemeGenerationLog(chat_id={self.chat_id}, success={self.success})>"

class DatabaseService:
    """
    Сервис для работы с базой данных.
    Если DATABASE_URL не указан, работает в режиме заглушки.
    """
    
    def __init__(self):
        self.enabled = bool(config.DATABASE_URL)
        self.engine = None
        self.session_maker = None
        
        if self.enabled:
            try:
                # Создаем асинхронный движок
                self.engine = create_async_engine(
                    config.DATABASE_URL,
                    pool_size=config.DB_POOL_SIZE,
                    max_overflow=config.DB_MAX_OVERFLOW,
                    echo=False  # Установите True для отладки SQL-запросов
                )
                
                # Создаем фабрику сессий
                self.session_maker = async_sessionmaker(
                    self.engine,
                    class_=AsyncSession,
                    expire_on_commit=False
                )
                
                logging.info("Database service initialized successfully")
            except Exception as e:
                logging.error(f"Failed to initialize database: {e}")
                self.enabled = False
        else:
            logging.info("Database is disabled (no DATABASE_URL provided)")
    
    async def init_db(self):
        """Инициализация таблиц в базе данных."""
        if not self.enabled:
            return
            
        try:
            async with self.engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logging.info("Database tables created successfully")
        except Exception as e:
            logging.error(f"Failed to create database tables: {e}")
    
    async def close(self):
        """Закрытие подключения к базе данных."""
        if self.enabled and self.engine:
            await self.engine.dispose()
            logging.info("Database connection closed")
    
    async def save_message(self, chat_id: int, message_id: int, user_id: Optional[int], 
                          username: Optional[str], text: str):
        """Сохранение сообщения в базу данных."""
        if not self.enabled:
            return
            
        try:
            async with self.session_maker() as session:
                message = ChatMessage(
                    chat_id=chat_id,
                    message_id=message_id,
                    user_id=user_id,
                    username=username,
                    text=text
                )
                session.add(message)
                await session.commit()
        except Exception as e:
            logging.error(f"Failed to save message to database: {e}")
    
    async def get_recent_messages(self, chat_id: int, limit: int = 10) -> List[ChatMessage]:
        """Получение последних сообщений из чата."""
        if not self.enabled:
            return []
            
        try:
            from sqlalchemy import select
            async with self.session_maker() as session:
                stmt = select(ChatMessage).where(
                    ChatMessage.chat_id == chat_id
                ).order_by(
                    ChatMessage.timestamp.desc()
                ).limit(limit)
                
                result = await session.execute(stmt)
                messages = result.scalars().all()
                return list(reversed(messages))  # Возвращаем в хронологическом порядке
        except Exception as e:
            logging.error(f"Failed to get messages from database: {e}")
            return []
    
    async def log_meme_generation(self, chat_id: int, user_id: Optional[int], 
                                 trigger_emoji: Optional[str], search_query: str,
                                 success: bool, error_message: Optional[str] = None,
                                 generation_time: Optional[float] = None):
        """Логирование генерации мема."""
        if not self.enabled:
            return
            
        try:
            async with self.session_maker() as session:
                log = MemeGenerationLog(
                    chat_id=chat_id,
                    user_id=user_id,
                    trigger_emoji=trigger_emoji,
                    search_query=search_query,
                    success=success,
                    error_message=error_message,
                    generation_time=generation_time
                )
                session.add(log)
                await session.commit()
        except Exception as e:
            logging.error(f"Failed to log meme generation: {e}")

# Глобальный экземпляр сервиса
db_service = DatabaseService()
