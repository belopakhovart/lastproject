import datetime
import sqlalchemy
from flask_login import UserMixin
from sqlalchemy import orm
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy_serializer import SerializerMixin

from .db_session import SqlAlchemyBase


class Indicators(SqlAlchemyBase, UserMixin, SerializerMixin):
    __tablename__ = 'indicators'

    id = sqlalchemy.Column(sqlalchemy.Integer,
                           primary_key=True, autoincrement=True)
    user = sqlalchemy.Column(sqlalchemy.String)
    temperature = sqlalchemy.Column(sqlalchemy.Float)
    contact_with_people = sqlalchemy.Column(sqlalchemy.Boolean)
    abroad = sqlalchemy.Column(sqlalchemy.Boolean)
    people_with_corona = sqlalchemy.Column(sqlalchemy.Boolean)
    do_user_know_about = sqlalchemy.Column(sqlalchemy.Boolean)
    self_isolatioon = sqlalchemy.Column(sqlalchemy.Boolean)
    address = sqlalchemy.Column(sqlalchemy.String)
