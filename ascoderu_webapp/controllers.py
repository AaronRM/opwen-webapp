from datetime import datetime

from ascoderu_webapp import app
from ascoderu_webapp import db
from ascoderu_webapp.models import Email
from ascoderu_webapp.models import User
from utils.strings import istreq


def _find_emails_by(user):
    def query_user_email():
        return Email.sender.ilike(user.email)

    def query_user_name():
        return Email.sender.ilike(user.name)

    if user.email and user.name:
        return query_user_email() | query_user_name()
    elif user.email:
        return query_user_email()
    elif user.name:
        return query_user_name()
    raise ValueError('one of user.email or user.name must be set')


def _find_user_by(name_or_email):
    if not name_or_email:
        return None

    return User.query.filter(User.name.ilike(name_or_email) |
                             User.email.ilike(name_or_email)).first()


def user_exists(name_or_email):
    user = _find_user_by(name_or_email)
    return user is not None


def outbox_emails_for(user):
    query = Email.date.is_(None) & _find_emails_by(user)
    return Email.query.filter(query).all()


def sent_emails_for(user):
    query = Email.date.isnot(None) & _find_emails_by(user)
    return Email.query.filter(query).all()


def inbox_emails_for(user):
    return [mail for mail in Email.query.all()
            if any(istreq(to, user.email) or istreq(to, user.name)
                   for to in mail.to)]


def new_email_for(user, to, subject, body):
    is_to_local_user = user_exists(to)
    email_date = datetime.utcnow() if is_to_local_user else None

    db.session.add(Email(
        date=email_date,
        to=[to],
        sender=user.email or user.name,
        subject=subject,
        body=body))
    db.session.commit()

    return is_to_local_user


def upload_local_updates():
    emails = Email.query.filter(Email.date.is_(None)).all()
    now = datetime.utcnow()
    for email in emails:
        email.date = now

    packed = app.remote_packer.pack(emails)
    serialized = app.remote_serializer.serialize(packed)
    app.remote_storage.upload(serialized)
    db.session.commit()

    return len(emails)


def download_remote_updates():
    serialized = app.remote_storage.download()
    packed = app.remote_serializer.deserialize(serialized)
    emails = app.remote_packer.unpack_emails(packed)
    accounts = app.remote_packer.unpack_accounts(packed)

    for email in emails:
        if email.is_complete():
            db.session.add(email)
    for name, email in accounts:
        user = _find_user_by(name)
        if user and name and email:
            user.name = name
            user.email = email
            db.session.add(user)
    db.session.commit()

    return len(emails)
