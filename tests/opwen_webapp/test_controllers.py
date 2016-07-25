from datetime import datetime

from flask_testing import TestCase

from opwen_webapp.controllers import download_remote_updates
from opwen_webapp.controllers import inbox_emails_for
from opwen_webapp.controllers import new_email_for
from opwen_webapp.controllers import outbox_emails_for
from opwen_webapp.controllers import sent_emails_for
from opwen_webapp.controllers import upload_local_updates
from opwen_webapp.controllers import user_exists
from opwen_webapp.models import Email
from opwen_webapp.models import User
from utils.testing import AppTestMixin


class TestUserExists(AppTestMixin, TestCase):
    def test_finds_user_by_name(self):
        name = 'some-name'
        self.new_user(name=name)

        self.assertTrue(user_exists(name))
        self.assertTrue(user_exists(name.upper()))

    def test_finds_user_by_email(self):
        email = 'someone@email.net'
        self.new_user(email=email)

        self.assertTrue(user_exists(email))
        self.assertTrue(user_exists(email.upper()))

    def test_does_not_find_non_existing_user(self):
        existing_name = 'some-name'
        non_existing_name = 'does-not-exist'
        self.new_user(name=existing_name)

        self.assertFalse(user_exists(non_existing_name))


# noinspection PyUnusedLocal,PyPep8Naming
class TestReadEmails(AppTestMixin, TestCase):
    def assertIterablesEqual(self, actual, expected):
        self.assertListEqual(list(actual), list(expected))

    def test_finds_inbox_emails_to_name_or_email(self):
        user = self.new_user(name='someone', email='someone@test.net')
        other_user = self.new_user(name='otherone', email='otherone@test.net')
        expected = [self.new_email(to=[user.name]),
                    self.new_email(to=[user.name.upper()]),
                    self.new_email(to=[user.email]),
                    self.new_email(to=[user.email.upper()]),
                    self.new_email(to=[user.name, other_user.name]),
                    self.new_email(to=[user.email, user.name]),
                    self.new_email(to=[user.email, user.email]),
                    self.new_email(to=[user.email, user.name, other_user.name])]
        not_expected = [self.new_email(to=[other_user.name]),
                        self.new_email(to=[other_user.email]),
                        self.new_email(to=[other_user.name.upper()])]
        actual = inbox_emails_for(user)

        self.assertIterablesEqual(actual, expected)

    def test_finds_sent_emails_to_name_or_email(self):
        now = datetime.utcnow()
        user = self.new_user(name='someone', email='someone@test.net')
        expected = [self.new_email(sender=user.name, date=now)]
        not_expected = [self.new_email(sender=user.name)]
        actual = sent_emails_for(user)

        self.assertIterablesEqual(actual, expected)

    def test_finds_outbox_emails_to_name_or_email(self):
        now = datetime.utcnow()
        user = self.new_user(name='someone', email='someone@test.net')
        expected = [self.new_email(sender=user.name)]
        not_expected = [self.new_email(sender=user.name, date=now)]
        actual = outbox_emails_for(user)

        self.assertIterablesEqual(actual, expected)


class TestWriteEmails(AppTestMixin, TestCase):
    def test_creates_new_email_for_local_user(self):
        sender = self.new_user(email='sender@test.net')
        recipient = self.new_user(name='ReciPienT', email='recipient@test.net')
        new_email_for(sender, recipient.name, 'subject', 'body')
        email = next(iter(Email.query.all()), None)

        self.assertIsNotNone(email)
        self.assertEqual(sender.email, email.sender)
        self.assertIn(recipient.name, email.to)
        self.assertEqual((datetime.utcnow() - email.date).days, 0)

    def test_creates_new_email_for_remote_user(self):
        sender = self.new_user(email='sender@test.net')
        recipient = 'recipient@test.net'
        new_email_for(sender, recipient, 'subject', 'body')
        email = next(iter(Email.query.all()), None)

        self.assertIsNotNone(email)
        self.assertEqual(sender.email, email.sender)
        self.assertIn(recipient, email.to)
        self.assertIsNone(email.date)


# noinspection PyUnusedLocal
class TestRemoteUpload(AppTestMixin, TestCase):
    def _retrieve_uploaded_emails(self, index):
        uploaded = self.app.remote_storage.uploaded[index]
        packed = self.app.remote_serializer.deserialize(uploaded)
        return self.app.remote_packer.unpack_emails(packed)

    def test_transmits_all_new_emails_without_resending_old_emails(self):
        new_emails = [self.new_email(), self.new_email(), self.new_email()]
        previously_sent_emails = [self.new_email(date=datetime.utcnow())]
        upload_local_updates()

        number_of_upload_calls = len(self.app.remote_storage.uploaded)
        self.assertEqual(number_of_upload_calls, 1)

        uploaded_emails = self._retrieve_uploaded_emails(0)
        for actual, expected in zip(uploaded_emails, new_emails):
            self.assertTrue(actual.is_same_as(expected))

        not_transmitted_emails = Email.query.filter(Email.date.is_(None))
        self.assertEqual(not_transmitted_emails.count(), 0)


class TestRemoteDownload(AppTestMixin, TestCase):
    def _prepare_serialized_data(self, data):
        serialized = self.app.remote_serializer.serialize(data)
        self.app.remote_storage.downloaded = serialized

    def _prepare_emails_for_download(self, emails):
        packed = self.app.remote_packer.pack(emails)
        self._prepare_serialized_data(packed)

    def _prepare_users_for_download(self, name, email):
        packed = {'accounts': [{'name': name, 'email': email}]}
        self._prepare_serialized_data(packed)

    def test_updates_emails(self):
        remote_emails = [self.create_complete_email() for _ in range(5)]
        self._prepare_emails_for_download(remote_emails)

        download_remote_updates()

        newly_updated_emails = Email.query.all()
        self.assertEqual(len(newly_updated_emails), len(remote_emails))
        for actual, expected in zip(newly_updated_emails, remote_emails):
            self.assertTrue(actual.is_same_as(expected))

    def test_updates_users_on_name(self):
        user, email = self.new_user(name='test'), 'test@opwen.net'
        self._prepare_users_for_download(user.name, email)

        download_remote_updates()

        updated_user = User.query.filter(User.name == user.name).first()
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.email, email)

    def test_updates_users_on_email(self):
        user, email = self.new_user(email='test'), 'test@opwen.net'
        self._prepare_users_for_download(user.email, email)

        download_remote_updates()

        updated_user = User.query.filter(User.name == user.name).first()
        self.assertIsNotNone(updated_user)
        self.assertEqual(updated_user.email, email)

    def test_ignores_corrupted_remote_data(self):
        self.app.remote_storage.downloaded = b'\xbe\xef'

        download_remote_updates()

        newly_updated_emails = Email.query.all()
        self.assertEqual(len(newly_updated_emails), 0)
