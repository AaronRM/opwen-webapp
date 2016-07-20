from flask import flash
from flask import redirect
from flask import render_template
from flask import request
from flask import url_for
from flask_security import current_user
from flask_security import login_required

from ascoderu_webapp import app
from ascoderu_webapp import babel
from ascoderu_webapp.controllers import inbox_emails_for
from ascoderu_webapp.controllers import new_email_for
from ascoderu_webapp.controllers import outbox_emails_for
from ascoderu_webapp.controllers import sent_emails_for
from ascoderu_webapp.forms import NewEmailForm
from config import LANGUAGES
from config import ui


@babel.localeselector
def get_locale():
    return request.accept_languages.best_match(LANGUAGES.keys())


@app.route('/')
def root():
    return redirect(url_for('home'))


@app.route('/home')
def home():
    return render_template('home.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/post_register')
@login_required
def post_register():
    user = current_user.name or current_user.email
    flash(ui('welcome_user', user=user), category='success')
    return redirect(url_for('home'))


@app.route('/post_login')
@login_required
def post_login():
    user = current_user.name or current_user.email
    flash(ui('welcome_back_user', user=user), category='success')
    return redirect(url_for('home'))


@app.route('/post_logout')
def post_logout():
    flash(ui('loggedout_user'), category='success')
    return redirect(url_for('home'))


@app.route('/email')
@login_required
def email():
    return redirect(url_for('email_inbox'))


@app.route('/email/new', methods=['GET', 'POST'])
@login_required
def email_new():
    form = NewEmailForm(request.form)
    if form.validate_on_submit():
        is_to_local_user = new_email_for(current_user, form.to.data,
                                         form.subject.data, form.body.data)
        message = ui('email_sent') if is_to_local_user else ui('email_delayed')
        next_endpoint = 'email_sent' if is_to_local_user else 'email_outbox'

        flash(message, category='success')
        return redirect(url_for(next_endpoint))

    return render_template('email_new.html', form=form)


@app.route('/email/inbox')
@login_required
def email_inbox():
    emails = inbox_emails_for(current_user)
    return render_template('email.html', emails=emails, is_outgoing=False)


@app.route('/email/outbox')
@login_required
def email_outbox():
    emails = outbox_emails_for(current_user)
    return render_template('email.html', emails=emails, is_outgoing=True)


@app.route('/email/sent')
@login_required
def email_sent():
    emails = sent_emails_for(current_user)
    return render_template('email.html', emails=emails, is_outgoing=True)
