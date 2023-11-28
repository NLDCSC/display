import logging
import time

import requests
from flask import redirect, url_for, abort
from flask_login import login_user

from display.helpers.app_logger import AppLogger
from display.webapp.app.models import Users, Groups, GroupMembers
from display.webapp.run import db, oidc, config
from . import auth
from ...core.general.constants import user_active
from ...core.general.utils import generate_random_password

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)


@auth.route("/oidc_login")
@oidc.require_login
def oidc_login():
    try:
        username = oidc.user_getfield("preferred_username")
        fullname = oidc.user_getfield("name")
    except AttributeError:
        logger.error(
            f"Missing 'preferred_username' and / or 'name' in access / ID token; these are required!"
        )
        oidc_logout()
        abort(401)

    try:
        resources = oidc.user_getfield("resources")
    except AttributeError:
        logger.error("Missing resources in OIDC ID token")
        oidc_logout()
        abort(401)

    allowed_resouces = config.ALLOWED_USER_GROUPS

    user_allowed = False
    for each in resources:
        if each in allowed_resouces:
            user_allowed = True
            break

    if not user_allowed:
        oidc_logout()
        abort(401)

    account = Users.query.filter_by(username=username, fullname=fullname).first()

    if account:
        # password validation is done by oidc; just log the user in
        account.last_login = int(time.time())

        db.session.add(account)
        db.session.commit()

        login_user(account)

        return redirect(url_for("home.index"))
    else:
        # nobody found; create user account; set keycloak rights and groups and log the user in
        new_user = Users()

        new_user.username = username
        new_user.fullname = fullname
        new_user.active = user_active.ENABLED

        # this account is created from openid; generate random password...
        new_user.password = generate_random_password()

        new_user.created = int(time.time())
        new_user.last_login = int(time.time())

        db.session.add(new_user)
        db.session.commit()

        # not yet in group; fetching group id
        new_group = Groups.query.filter_by(name="user").first()
        group_id = new_group.id

        db.session.add(GroupMembers(group=group_id, user=new_user.id))
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("home.index"))


def oidc_logout():
    try:
        with requests.session() as session:

            headers = {
                "Authorization": f"Bearer {oidc.get_access_token()}",
                "Content-Type": "application/x-www-form-urlencoded",
            }

            data = {
                "client_id": f"{oidc.client_secrets.get('client_id')}",
                "client_secret": f"{oidc.client_secrets.get('client_secret')}",
                "refresh_token": f"{oidc.get_refresh_token()}",
            }

            session.post(
                url=f"{oidc.client_secrets.get('issuer')}/protocol/openid-connect/logout",
                data=data,
                headers=headers,
                verify=False,
            )

        oidc.logout()
    except TypeError:
        pass
