from os import remove
from tempfile import NamedTemporaryFile

from flask_testing import TestCase

from opwen_email_client.config import FlaskConfig
from opwen_email_client.ioc import create_app


class TestConfig(FlaskConfig):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite://'
    SECURITY_PASSWORD_SALT = 'UnSalted'
    SECRET_KEY = 'NoSecret'

    def __init__(self):
        with NamedTemporaryFile(delete=False) as fobj:
            self.LOCAL_EMAIL_STORE = fobj.name

    def close(self):
        remove(self.LOCAL_EMAIL_STORE)


class Base(object):
    class AppTests(TestCase):
        def _pre_setup(self):
            self.app_config = TestConfig()
            super()._pre_setup()

        def _post_teardown(self):
            self.app_config.close()
            super()._post_teardown()

        def create_app(self):
            app = create_app()
            app.config.from_object(self.app_config)
            return app
