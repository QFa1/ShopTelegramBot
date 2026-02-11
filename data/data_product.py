import sqlalchemy
from .db_session import SqlAlchemyBase
from sqlalchemy_serializer import SerializerMixin


class Data_Product(SqlAlchemyBase, SerializerMixin):
    __tablename__ = 'data_product'
    id = sqlalchemy.Column(sqlalchemy.Integer, primary_key=True, autoincrement=True)
    product_id = sqlalchemy.Column(sqlalchemy.Integer, sqlalchemy.ForeignKey("products.id"), nullable=False)
    data = sqlalchemy.Column(sqlalchemy.String, nullable=False)
    purchased = sqlalchemy.Column(sqlalchemy.Boolean, default=False)
