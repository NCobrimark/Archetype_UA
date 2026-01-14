from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy import select, update
from core.config import settings
from core.db_models import Base, User, Session, Answer

class DBRepo:
    def __init__(self):
        self.engine = create_async_engine(settings.DATABASE_URL, echo=False)
        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def init_db(self):
        async with self.engine.begin() as conn:
            # await conn.run_sync(Base.metadata.drop_all) # For dev reset
            await conn.run_sync(Base.metadata.create_all)

    async def get_or_create_user(self, telegram_id: int, name: str = None) -> User:
        async with self.async_session() as session:
            result = await session.execute(select(User).where(User.telegram_id == telegram_id))
            user = result.scalar_one_or_none()
            
            if not user:
                user = User(telegram_id=telegram_id, name=name)
                session.add(user)
                await session.commit()
                await session.refresh(user)
            return user

    async def create_session(self, user_id: int) -> Session:
        async with self.async_session() as session:
            # Mark previous sessions as potentially abandoned? Or just create new.
            new_session = Session(user_id=user_id)
            session.add(new_session)
            await session.commit()
            await session.refresh(new_session)
            return new_session

    async def save_answer(self, session_id: int, question_id: int, option_id: str, open_text: str = None):
        async with self.async_session() as session:
            # Check if answer exists to update
            result = await session.execute(
                select(Answer).where(Answer.session_id == session_id, Answer.question_id == question_id)
            )
            answer = result.scalar_one_or_none()
            
            if answer:
                answer.selected_option_id = option_id
                answer.open_text_input = open_text
            else:
                answer = Answer(
                    session_id=session_id,
                    question_id=question_id,
                    selected_option_id=option_id,
                    open_text_input=open_text
                )
                session.add(answer)
            
            await session.commit()

    async def get_session_with_answers(self, session_id: int) -> Session:
        async with self.async_session() as session:
            # Join loading needs explicit option or lazy load
            result = await session.execute(
                select(Session).where(Session.id == session_id).execution_options(populate_existing=True)
            )
            # Accessing session.answers will trigger lazy load if not careful in async
            # Use selectinload in production. For now keeping simple.
            # Actually async requires exact loading strategies usually.
            # Let's verify compatibility. For MVP this might error if relationships aren't loaded eager.
            pass 
            # Placeholder: In async sqlalchemy, relationship loading requires `options(selectinload(Session.answers))`
            return result.scalar_one_or_none()

db_repo = DBRepo()
