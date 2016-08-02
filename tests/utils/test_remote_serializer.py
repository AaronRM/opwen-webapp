from unittest import TestCase

from tests.app_base import AppTestMixin
from tests.base import FileWritingTestCaseMixin
from utils.compressor import ZipCompressor
from utils.fileformatter import JsonLines
from utils.remote_serializer import RemoteSerializer


class TestRemoteSerializer(FileWritingTestCaseMixin, AppTestMixin, TestCase):
    def setUp(self):
        AppTestMixin.setUp(self)
        FileWritingTestCaseMixin.setUp(self)

    def tearDown(self):
        AppTestMixin.tearDown(self)
        FileWritingTestCaseMixin.tearDown(self)

    def assertAccountsEqual(self, actual, expected):
        """
        :type actual: collections.Iterable[opwen_webapp.models.User]
        :type expected: collections.Iterable[opwen_webapp.models.User]

        """
        for actual, expected in zip(actual, expected):
            self.assertEqual(actual.name, expected.name)
            self.assertEqual(actual.email, expected.email)

    def assertEmailsEqual(self, actual, expected):
        """
        :type actual: collections.Iterable[opwen_webapp.models.Email]
        :type expected: collections.Iterable[opwen_webapp.models.Email]

        """
        for actual, expected in zip(actual, expected):
            self.assertTrue(actual.is_same_as(expected))

    @property
    def serializer(self):
        """
        :rtype: RemoteSerializer

        """
        return RemoteSerializer(JsonLines, ZipCompressor, self.create_app())

    def test_serialization_deserialization_roundtrip_for_emails(self):
        expected_emails = [self.create_complete_email() for _ in range(5)]

        serialized = self.serializer.serialize(expected_emails)
        actual_emails, actual_accounts = self.serializer.deserialize(serialized)

        self.paths_created.add(serialized)
        self.assertEqual(actual_accounts, [])
        self.assertEmailsEqual(actual_emails, expected_emails)

    def test_serialization_deserialization_roundtrip_for_accounts(self):
        expected_accounts = [self.create_complete_user() for _ in range(5)]

        serialized = self.serializer.serialize(accounts=expected_accounts)
        actual_emails, actual_accounts = self.serializer.deserialize(serialized)

        self.paths_created.add(serialized)
        self.assertEqual(actual_emails, [])
        self.assertAccountsEqual(actual_accounts, expected_accounts)

    def test_deserializer_handles_corrupt_archive(self):
        serialized = self.new_file(content='not-a-zip-file')

        emails, accounts = self.serializer.deserialize(serialized)

        self.assertEqual(emails, [])
        self.assertEqual(accounts, [])
