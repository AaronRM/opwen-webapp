from flask import Flask
from flask_babel import Babel
from flask_migrate import Migrate
from flask_security import SQLAlchemyUserDatastore
from flask_security import Security
from flask_sqlalchemy import SQLAlchemy

from config import Config
from utils.remote_storage import AzureBlob
from utils.serialization import CompressedJson
from utils.uploads import Uploads

app = Flask(__name__)
app.config.from_object(Config)

babel = Babel(app)

db = SQLAlchemy(app)
migrate = Migrate(app, db)

uploads = Uploads(app)

from utils import jinja_filters

app.jinja_env.filters['safe_multiline'] = jinja_filters.safe_multiline
app.jinja_env.filters['render_date'] = jinja_filters.render_date
app.jinja_env.filters['sort_by_date'] = jinja_filters.sort_by_date
app.jinja_env.filters['ui'] = jinja_filters.ui
app.jinja_env.filters['is_admin'] = jinja_filters.is_admin
app.jinja_env.filters['attachment_url'] = jinja_filters.attachment_url

from opwen_webapp import views
from opwen_webapp import models
from opwen_webapp import forms

app.remote_serializer = CompressedJson()
app.remote_packer = models.ModelPacker()
app.remote_storage = AzureBlob(
    account_name=Config.REMOTE_STORAGE_ACCOUNT_NAME,
    account_key=Config.REMOTE_STORAGE_ACCOUNT_KEY,
    container=Config.REMOTE_STORAGE_CONTAINER,
    upload_path=Config.REMOTE_UPLOAD_PATH,
    download_path=Config.REMOTE_DOWNLOAD_PATH,
    upload_format=Config.REMOTE_UPLOAD_FORMAT)

user_datastore = SQLAlchemyUserDatastore(db, models.User, models.Role)
security = Security(app, user_datastore,
                    login_form=forms.LoginForm,
                    register_form=forms.RegisterForm)

db.create_all()

from opwen_webapp import handlers
