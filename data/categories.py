import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Categories(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'categories'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    category = sqlalchemy.Column(sqlalchemy.String, nullable=False)
