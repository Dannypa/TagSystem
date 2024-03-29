from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import sessionmaker
import config

engine = create_engine(f'sqlite:///{config.TABLENAME}.db?check_same_thread=False')  # creating a database file

Base = declarative_base()  # parent class for our Table class


class Tags(Base):
    __tablename__ = config.TABLENAME  # name in database
    # primary key means that id will define object (i guess?)
    id = Column(Integer, primary_key=True)
    path = Column(String, default='')
    tags = Column(String, default='')

    def __init__(self, path, tags):
        self.path = path
        self.tags = tags

    def __str__(self) -> str:
        return f"path: {self.path}; tags: {list(self.tags.split(config.tag_delimiter))}"

    def __repr__(self) -> str:
        return f"id: {self.id}; path: {self.path}; tags: {list(self.tags.split(config.tag_delimiter))}"


Base.metadata.create_all(engine)  # creating database

Session = sessionmaker(bind=engine)  # creating this to work with the database
session = Session()  # to manage database
