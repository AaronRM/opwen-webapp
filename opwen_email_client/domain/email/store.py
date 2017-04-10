from abc import ABCMeta
from abc import abstractmethod
from datetime import datetime
from uuid import uuid4

from sqlalchemy import Binary
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy import ForeignKey
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import Table
from sqlalchemy import Text
from sqlalchemy import exists
from sqlalchemy import or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.orm import sessionmaker

from opwen_email_client.util.sqlalchemy import create_database
from opwen_email_client.util.sqlalchemy import get_or_create
from opwen_email_client.util.sqlalchemy import session


_Base = declarative_base()


_EmailTo = Table('emailto',
                 _Base.metadata,
                 Column('email_id', Integer, ForeignKey('email.id')),
                 Column('to_id', Integer, ForeignKey('to.id')))

_EmailCc = Table('emailcc',
                 _Base.metadata,
                 Column('email_id', Integer, ForeignKey('email.id')),
                 Column('cc_id', Integer, ForeignKey('cc.id')))

_EmailBcc = Table('emailbcc',
                  _Base.metadata,
                  Column('email_id', Integer, ForeignKey('email.id')),
                  Column('bcc_id', Integer, ForeignKey('bcc.id')))


class _To(_Base):
    __tablename__ = 'to'
    id = Column(Integer, primary_key=True)

    address = Column(String(length=128), index=True, unique=True)


class _Cc(_Base):
    __tablename__ = 'cc'
    id = Column(Integer, primary_key=True)

    address = Column(String(length=128), index=True, unique=True)


class _Bcc(_Base):
    __tablename__ = 'bcc'
    id = Column(Integer, primary_key=True)

    address = Column(String(length=128), index=True, unique=True)


class _Email(_Base):
    __tablename__ = 'email'
    id = Column(Integer, primary_key=True)

    uid = Column(String(length=64), unique=True, index=True)
    subject = Column(Text)
    body = Column(Text)
    sent_at = Column(String(length=64))
    read = Column(Boolean, default=False, nullable=False)
    sender = Column(String(length=128), index=True)
    attachments = Column(Binary)
    to = relationship(_To, secondary=_EmailTo)
    cc = relationship(_Cc, secondary=_EmailCc)
    bcc = relationship(_Bcc, secondary=_EmailBcc)

    def to_dict(self, serializer):
        attachments = self.attachments
        attachments = serializer.deserialize(attachments) if attachments else None

        return {k: v for (k, v) in (
            ('from', self.sender),
            ('to', [_.address for _ in self.to]),
            ('cc', [_.address for _ in self.cc]),
            ('bcc', [_.address for _ in self.bcc]),
            ('subject', self.subject),
            ('body', self.body),
            ('_uid', self.uid),
            ('sent_at', self.sent_at),
            ('read', self.read),
            ('attachments', attachments),
        ) if v}

    @classmethod
    def from_dict(cls, db, serializer, email):
        attachments = email.get('attachments')
        attachments = serializer.serialize(attachments) if attachments else None

        return _Email(
            uid=email['_uid'],
            to=[get_or_create(db, _To, address=_) for _ in email.get('to', [])],
            cc=[get_or_create(db, _Cc, address=_) for _ in email.get('cc', [])],
            bcc=[get_or_create(db, _Bcc, address=_) for _ in email.get('bcc', [])],
            subject=email.get('subject'),
            body=email.get('body'),
            sent_at=email.get('sent_at'),
            read=email.get('read', False),
            attachments=attachments,
            sender=email.get('from'))

    @classmethod
    def is_sent_by(cls, email_address):
        return cls.sender.ilike(email_address)

    @classmethod
    def is_received_by(cls, email_address):
        return (cls.to.any(_To.address.ilike(email_address)) |
                cls.cc.any(_Cc.address.ilike(email_address)) |
                cls.bcc.any(_Bcc.address.ilike(email_address)))


class EmailStore(metaclass=ABCMeta):
    def create(self, emails):
        """
        :type emails: collections.Iterable[dict]

        """
        self._create(map(self._add_uid, emails))

    @abstractmethod
    def _create(self, emails):
        """
        :type emails: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def get(self, uid):
        """
        :type uid: str
        :rtype dict | None

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def inbox(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def outbox(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def sent(self, email_address):
        """
        :type email_address: str
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def search(self, email_address, query):
        """
        :type email_address: str
        :type query: str | None
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def pending(self):
        """
        :rtype: collections.Iterable[dict]

        """
        raise NotImplementedError  # pragma: no cover

    def mark_sent(self, emails_or_uids):
        """
        :type emails_or_uids: collections.Iterable[dict] | collections.Iterable[str]

        """
        uids = map(self._get_uid, emails_or_uids)
        return self._mark_sent(uids)

    def mark_read(self, email_address, emails_or_uids):
        """
        :type email_address: str
        :type emails_or_uids: collections.Iterable[dict] | collections.Iterable[str]

        """
        uids = map(self._get_uid, emails_or_uids)
        return self._mark_read(email_address, uids)

    @abstractmethod
    def _mark_sent(self, uids):
        """
        :type uids: collections.Iterable[str]

        """
        raise NotImplementedError  # pragma: no cover

    @abstractmethod
    def _mark_read(self, email_address, uids):
        """
        :type email_address: str
        :type uids: collections.Iterable[str]

        """
        raise NotImplementedError  # pragma: no cover

    @classmethod
    def _get_uid(cls, email_or_uid):
        """
        :type email_or_uid: dict | str
        :rtype: str

        """
        try:
            return email_or_uid['_uid']
        except TypeError:
            return email_or_uid

    @classmethod
    def _add_uid(cls, email):
        """
        :type email: dict
        :rtype: dict

        """
        email.setdefault('_uid', str(uuid4()))
        return email


class _SqlalchemyEmailStore(EmailStore):
    def __init__(self, database_uri, serializer):
        """
        :type database_uri: str
        :type serializer: opwen_infrastructure.serialization.Serializer

        """
        self._serializer = serializer
        self._base = _Base
        self._engine = create_database(database_uri, self._base)
        self._sesion_maker = sessionmaker(autocommit=False, autoflush=False,
                                          bind=self._engine)

    def _dbread(self):
        return session(self._sesion_maker, commit=False)

    def _dbwrite(self):
        return session(self._sesion_maker, commit=True)

    def _create(self, emails):
        with self._dbwrite() as db:
            for email in emails:
                uid_exists = exists().where(_Email.uid == email['_uid'])
                if not db.query(uid_exists).scalar():
                    db.add(_Email.from_dict(db, self._serializer, email))

    def _mark_sent(self, uids):
        set_sent_at = {_Email.sent_at: datetime.utcnow().strftime('%Y-%m-%d %H:%M')}
        match_email_uid = or_(*(_Email.uid == uid for uid in uids))

        with self._dbwrite() as db:
            db.query(_Email).filter(match_email_uid)\
                .update(set_sent_at)

    def _mark_read(self, email_address, uids):
        set_read = {_Email.read: True}
        match_email_uid = or_(*(_Email.uid == uid for uid in uids))
        can_access = _Email.is_sent_by(email_address) | _Email.is_received_by(email_address)

        with self._dbwrite() as db:
            db.query(_Email).filter(match_email_uid & can_access)\
                .update(set_read, synchronize_session='fetch')

    def _find(self, query):
        with self._dbread() as db:
            results = db.query(_Email).filter(query)
            email = results.first()
            return email.to_dict(self._serializer) if email else None

    def _query(self, query):
        with self._dbread() as db:
            results = db.query(_Email).filter(query)
            for email in results.all():
                yield email.to_dict(self._serializer)

    def inbox(self, email_address):
        return self._query(_Email.is_received_by(email_address))

    def outbox(self, email_address):
        return self._query(_Email.is_sent_by(email_address) & _Email.sent_at.is_(None))

    def search(self, email_address, query):
        textquery = '%{}%'.format(query)
        contains_query = or_(*(_Email.subject.ilike(textquery),
                               _Email.body.ilike(textquery),
                               _Email.is_received_by(textquery),
                               _Email.is_sent_by(textquery)))
        can_access = _Email.is_received_by(email_address) | _Email.is_sent_by(email_address)
        return self._query(can_access & contains_query)

    def pending(self):
        return self._query(_Email.sent_at.is_(None))

    def get(self, uid):
        return self._find(_Email.uid == uid)

    def sent(self, email_address):
        return self._query(_Email.is_sent_by(email_address) & _Email.sent_at.isnot(None))


class SqliteEmailStore(_SqlalchemyEmailStore):
    def __init__(self, database_path, serializer):
        """
        :type database_path: str
        :type serializer: opwen_infrastructure.serialization.Serializer

        """
        super().__init__('sqlite:///{}'.format(database_path), serializer)
