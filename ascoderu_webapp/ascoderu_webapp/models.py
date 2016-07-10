from flask_security import RoleMixin
from flask_security import UserMixin
from sqlalchemy_utils import ScalarListType

from ascoderu_webapp import db

roles_users = db.Table(
    'roles_users',
    db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
    db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))


class User(db.Model, UserMixin):
    id = db.Column(db.Integer(), primary_key=True)
    email = db.Column(db.String(255), unique=True, index=True)
    password = db.Column(db.String(255), nullable=False)
    active = db.Column(db.Boolean(), default=True)

    name = db.Column(db.String(255), unique=True, index=True)

    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

    @classmethod
    def exists(cls, name_or_email):
        return User.query.filter(
            User.name.ilike(name_or_email) | User.email.ilike(name_or_email)
        ).first() is not None


class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))


class Email(db.Model):
    id = db.Column(db.Integer(), primary_key=True)
    date = db.Column(db.DateTime(timezone=True))
    sender = db.Column(db.String(255), nullable=False)
    to = db.Column(ScalarListType(), nullable=False)
    subject = db.Column(db.String())
    body = db.Column(db.String())
