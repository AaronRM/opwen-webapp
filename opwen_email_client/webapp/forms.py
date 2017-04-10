from typing import Optional as Maybe, Iterable
from typing import List

from flask import render_template
from flask import request
from flask_login import current_user
from flask_wtf import Form
from werkzeug.datastructures import FileStorage
from wtforms import FileField
from wtforms import StringField
from wtforms import SubmitField
from wtforms.validators import DataRequired
from wtforms.validators import Email
from wtforms.validators import Optional

from opwen_email_client.domain.email.attachment import AttachmentEncoder
from opwen_email_client.domain.email.store import EmailStore
from opwen_email_client.util.wtforms import EmailField
from opwen_email_client.util.wtforms import HtmlTextAreaField
from opwen_email_client.webapp.config import AppConfig
from opwen_email_client.webapp.config import i8n


class NewEmailForm(Form):
    to = EmailField(
        validators=[DataRequired(i8n.EMAIL_TO_REQUIRED),
                    Email(i8n.EMAIL_ADDRESS_INVALID)])

    cc = EmailField(
        validators=[Optional(),
                    Email(i8n.EMAIL_ADDRESS_INVALID)])

    bcc = EmailField(
        validators=[Optional(),
                    Email(i8n.EMAIL_ADDRESS_INVALID)])

    subject = StringField(
        validators=[Optional()])

    body = HtmlTextAreaField(
        validators=[Optional()])

    attachments = FileField(
        validators=[Optional()],
        render_kw={'multiple': True})

    submit = SubmitField()

    def _handle_reply(self, email: dict):
        self.to.data = email.get('from', '')
        self.subject.data = 'Re: {}'.format(email.get('subject', ''))

    def _handle_reply_all(self, email: dict):
        self.to.data = _join_emails(email.get('from'), *email.get('cc', []))
        self.subject.data = 'Re: {}'.format(email.get('subject', ''))

    def _handle_forward(self, email: dict):
        self.subject.data = 'Fwd: {}'.format(email.get('subject', ''))
        self.body.data = render_template('emails/forward.html', email=email)

    def handle_action(self, email_store: EmailStore):
        uid = request.args.get('uid')
        action = request.args.get('action')
        if not uid or not action:
            return

        reference = email_store.get(uid)
        if not reference or not current_user.can_access(reference):
            return

        if action == 'reply':
            self._handle_reply(reference)
        elif action == 'reply_all':
            self._handle_reply_all(reference)
        elif action == 'forward':
            self._handle_forward(reference)

    def as_dict(self, attachment_encoder: AttachmentEncoder) -> dict:
        attachments = request.files.getlist(self.attachments.name)
        form = {key: value for (key, value) in self.data.items() if value}
        form.pop('submit', None)
        form['sent_at'] = None
        form['read'] = True
        form['from'] = current_user.email
        form['to'] = _split_emails(form.get('to'))
        form['cc'] = _split_emails(form.get('cc'))
        form['bcc'] = _split_emails(form.get('bcc'))
        form['body'] = form.get('body')
        form['attachments'] = list(_attachments_as_dict(attachments,
                                                        attachment_encoder))
        return form

    @classmethod
    def from_request(cls, email_store: EmailStore):
        form = cls(request.form)
        form.handle_action(email_store)
        return form


def _attachments_as_dict(
        filestorages: Iterable[FileStorage],
        attachment_encoder: AttachmentEncoder) -> Iterable[dict]:

    for filestorage in filestorages:
        filename = filestorage.filename
        content = attachment_encoder.encode(filestorage.stream.read())
        if filename and content:
            yield {'filename': filename, 'content': content}


def _join_emails(*emails: str) -> str:
    delimiter = '{0} '.format(AppConfig.EMAIL_ADDRESS_DELIMITER)
    return delimiter.join(email for email in emails if email)


def _split_emails(emails: Maybe[str]) -> List[str]:
    if not emails:
        return []

    addresses = emails.split(AppConfig.EMAIL_ADDRESS_DELIMITER)
    return [address.strip() for address in addresses]
