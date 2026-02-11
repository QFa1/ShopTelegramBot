import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Products(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'products'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    categ_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("categories.id"), nullable=False)
    name = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    price = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    count = sqlalchemy.Column(sqlalchemy.Integer, default=0)
    image_path = sqlalchemy.Column(sqlalchemy.String, nullable=True)
    description = sqlalchemy.Column(sqlalchemy.String, nullable=True)
