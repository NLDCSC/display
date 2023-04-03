from flask import render_template, redirect, url_for
from flask_login import current_user, login_user, login_required, logout_user

from display.webapp.app.models import users
from . import auth
from .forms import LoginForm
from ..run import login_manager, config


@login_manager.user_loader
def load_user(user_id):
    user = users.query.filter_by(id=user_id).first()

    return user


@auth.route("/login", methods=["GET", "POST"])
def func_login():

    header = "Display login"

    if current_user.is_authenticated:
        return redirect(url_for("home.index"))
    form = LoginForm()
    if form.validate_on_submit():

        # Check if account exists
        account = users.query.filter_by(username=form.username.data).first()

        if account and account.verify_password(form.password.data):
            login_user(account)

            return redirect(url_for("home.index"))
        else:
            msg = "Incorrect username/password!"
            return render_template("login.html", header=header, form=form, msg=msg, openid=config.OPENID_LOGIN)

    return render_template("login.html", header=header, form=form, openid=config.OPENID_LOGIN)


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
