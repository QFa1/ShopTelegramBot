import datetime
import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class User(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'users'
    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user_tg_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=False, index=True, unique=True)
    user_login = sqlalchemy.Column(sqlalchemy.Text, nullable=False)
    balance = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    all_money = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    modified_date = sqlalchemy.Column(sqlalchemy.DateTime, default=datetime.datetime.now)
    purchases = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    count_refer = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    refer_id = sqlalchemy.Column(sqlalchemy.Integer, nullable=True)
    received_from_ref = sqlalchemy.Column(sqlalchemy.Integer, default=0)
