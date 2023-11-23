import time

from flask import render_template, redirect, url_for
from flask_login import current_user, login_user, login_required, logout_user

from display.webapp.app.models import Users
from . import auth
from .forms import LoginForm
from ..run import login_manager, config, db
from ...core.general.constants import user_active, user_type


@login_manager.user_loader
def load_user(user_id):
    user = (
        Users.query.filter_by(id=user_id)
        .filter(Users.active != user_active.DISABLED)
        .filter(Users.system != user_type.SYSTEM)
        .first()
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
        account = Users.query.filter_by(username=form.username.data).first()

        if account and account.verify_password(form.password.data):
            login_user(account)

            return redirect(url_for("home.index"))
        else:
            msg = "Incorrect username/password!"
            return render_template(
                "login.html",
                header=header,
                form=form,
                msg=msg,
                openid=config.OPENID_LOGIN,
            )

    return render_template(
        "login.html", header=header, form=form, openid=config.OPENID_LOGIN
    )


@auth.route("/logout")
@login_required
def logout():
    logout_user()

    if config.OPENID_LOGIN:
        try:
            from .openid_login import oidc_logout

            oidc_logout()
        except ImportError:
            pass
        except TypeError:
            pass

    return redirect(url_for("auth.func_login"))


@auth.route("/create_api_key")
@login_required
def create_api_key():
    this_user = Users.query.filter_by(username=current_user.username).first()

    if this_user is not None:
        the_key = this_user.create_api_key()
        this_user.apikey = the_key
        this_user.updated = int(time.time())

        db.session.add(this_user)
        db.session.commit()

        return render_template("partials/api-key.html", api_key=the_key)

    else:
        return render_template("partials/api-key.html")
