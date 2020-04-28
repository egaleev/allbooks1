import datetime
import sqlalchemy
from sqlalchemy import orm

from .db_session import SqlAlchemyBase


class Reserve(SqlAlchemyBase):
    __tablename__ = 'reserve'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_name = sqlalchemy.Column(sqlalchemy.Integer,
                                  sqlalchemy.ForeignKey("users.name"))
    book_name = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("posts.title"))
    time = sqlalchemy.Column(sqlalchemy.Date)

    def __repr__(self):
        return f'Reserve by {self.user_name} > {self.book_name} at {self.time}'
