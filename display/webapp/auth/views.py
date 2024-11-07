import time

from flask import render_template, redirect, url_for
from flask_login import current_user, login_user, login_required, logout_user
from sqlalchemy import select

from display.webapp.app.models import Users
from . import auth
from .forms import LoginForm
from ..run import login_manager, config, db
from ...core.general.constants import user_active, user_type


@login_manager.user_loader
def load_user(user_id):
    user = db.session.scalar(
        select(Users).filter(
            Users.active != user_active.DISABLED,
            Users.system != user_type.SYSTEM,
            Users.id == user_id,
        )
    )

    return user


@auth.route("/login", methods=["GET", "POST"])
def func_login():

    header = "Display login"

    if current_user.is_authenticated:
        return redirect(url_for("home.index"))
    form = LoginForm()
    if form.validate_on_submit():

        # Check if account exists
        account = db.session.scalar(
            select(Users).filter(Users.username == form.username.data)
        )

        if account and account.verify_password(form.password.data):
            account.last_login = int(time.time())

            db.session.add(account)
            db.session.commit()

            login_user(account)

            return redirect(url_for("home.index"))
        else:
            msg = "Incorrect username/password!"
            return render_template(
                "login.html",
                header=header,
                form=form,
                msg=msg,
                openid=config.SSO_LOGIN_ENABLE,
            )

    return render_template(
        "login.html", header=header, form=form, openid=config.SSO_LOGIN_ENABLE
    )


@auth.route("/logout")
@login_required
def logout():
    if config.SSO_LOGIN_ENABLE:
        from display.webapp.run import sso

        sso.logout()

    logout_user()

    return redirect(url_for("auth.func_login"))


@auth.route("/create_api_key")
@login_required
def create_api_key():
    this_user = db.session.scalar(
        select(Users).filter(Users.username == current_user.username)
    )

    if this_user is not None:
        the_key = this_user.create_api_key()
        this_user.apikey = the_key
        this_user.updated = int(time.time())

        db.session.add(this_user)
        db.session.commit()

        return render_template("partials/api-key.html", api_key=the_key)

    else:
        return render_template("partials/api-key.html")
