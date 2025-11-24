from sqlalchemy import create_engine
from sqlalchemy.orm import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import Session
from sqlalchemy import ForeignKey, select, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column,relationships
from dotenv import load_dotenv
import os

load_dotenv()

database_url = os.getenv("DATABASE_URL")

print(f"Database URL: {database_url}")

engine = create_engine(database_url)

class Base(DeclarativeBase):
        pass

class Whole_Blogs(Base):

    __tablename__ = "travel_blogs"

    id: Mapped[int] = mapped_column(primary_key=True)
    blog_url: Mapped[str]
    page_url: Mapped[str] = mapped_column(unique=True, nullable=False)
    page_title: Mapped[str]
    page_description: Mapped[str]
    page_author: Mapped[str]
    location_name: Mapped[str]
    latitude: Mapped[float]
    longitude: Mapped[float]
    content: Mapped[str]

    def __repr__(self) -> str:
        return f"Whole_Blogs(id={self.id!r}, , location_name={self.location_name!r}, page_title={self.page_title!r}"


# with Session(engine) as session:
    # posts = session.query(Whole_Blogs).all()
    # print(posts)

with Session(engine) as session:
    count = session.execute(
        select(func.count()).select_from(Whole_Blogs)
    ).scalar_one()
    print("Number of Items:", count)



