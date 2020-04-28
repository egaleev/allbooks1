import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Post(SqlAlchemyBase):
    __tablename__ = 'posts'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    title = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    content = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    created_date = sqlalchemy.Column(sqlalchemy.DateTime,
                                     default=datetime.datetime.now)
    available = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    file = sqlalchemy.Column(sqlalchemy.String)
    pic = sqlalchemy.Column(sqlalchemy.String)

    def __repr__(self):
        return f'{self.id}, {self.title}, {self.content}'
