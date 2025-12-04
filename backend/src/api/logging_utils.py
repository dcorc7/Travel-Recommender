import logging
from sqlalchemy import create_engine
from sqlalchemy import ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationships
from sqlalchemy import Column, Integer, String, Date
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from dotenv import load_dotenv
import os

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

def db_connect_logging():
    engine = create_engine(DATABASE_URL)

    class Base(DeclarativeBase):
        pass

    class Logging(Base):

        __tablename__ = "app_logs"

        id: Mapped[int] = mapped_column(primary_key=True)
        log_date: Mapped[Date] = mapped_column(unique=True, nullable=False)
        content: Mapped[str]

        def __repr__(self) -> str:
            return f"Log(id={self.id!r}, , date={self.log_date!r}, content={self.content!r}"

    # This actually creates the table
    Base.metadata.create_all(engine)

    return engine, Logging


def main():
    logging.basicConfig(level=logging.INFO,
                        format="%(asctime)s - %(levelname)s - %(message)s")
    logger = logging.getLogger("travel-data")
    return logger

if __name__ == "__main__":
    main()