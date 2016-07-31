from os import makedirs
from os import path
from os import rename
from tempfile import NamedTemporaryFile

from utils.checksum import sha256

SCRIPTS = frozenset('.js .php .pl .py .rb .sh'.split())
EXECUTABLES = frozenset('.so .exe .dll'.split())


class UploadNotAllowed(Exception):
    pass


class Uploads(object):
    def __init__(self, app=None, directory=None, disallowed=None, hasher=None):
        """
        :type app: flask.Flask
        :type directory: str
        :type disallowed: collections.Iterable[str]

        """
        self.app = app
        self.root_directory = directory or app.config.get('UPLOAD_DIRECTORY')
        self.disallowed = frozenset(disallowed or SCRIPTS | EXECUTABLES)
        self.hasher = hasher or sha256

    def _check_upload_allowed(self, upload):
        """
        :type upload: werkzeug.datastructures.FileStorage
        :raises UploadNotAllowed

        """
        extension = path.splitext(upload.filename)[1]
        if extension in self.disallowed:
            raise UploadNotAllowed

    @classmethod
    def _save_to_temporary_location(cls, upload):
        """
        :type upload: werkzeug.datastructures.FileStorage
        :rtype: str

        """
        with NamedTemporaryFile('w', delete=False) as tmpfile:
            upload.save(tmpfile.name)
        return tmpfile.name

    @classmethod
    def _move_to(cls, from_path, to_path):
        """
        :type from_path: str
        :type to_path: str

        """
        makedirs(path.dirname(to_path), mode=0o700, exist_ok=True)
        rename(from_path, to_path)

    def _move_to_upload_directory(self, uploaded_filename):
        """
        :type uploaded_filename: str
        :rtype: str

        """
        upload_location = path.join(self.root_directory,
                                    self.hasher(uploaded_filename))
        self._move_to(uploaded_filename, upload_location)
        return upload_location

    def save(self, upload):
        """
        :type upload: werkzeug.datastructures.FileStorage
        :rtype: str
        :raises UploadNotAllowed

        """
        self._check_upload_allowed(upload)

        temporary_filename = self._save_to_temporary_location(upload)

        return self._move_to_upload_directory(temporary_filename)
