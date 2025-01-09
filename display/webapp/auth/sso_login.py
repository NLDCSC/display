import logging
import time

from flask import redirect, url_for, abort
from flask_login import login_user
from nldcsc.generic.utils import generate_random_password
from nldcsc.loggers.app_logger import AppLogger
from sqlalchemy import select

from display.webapp.app.models import Users, Groups, GroupMembers
from display.webapp.run import db, sso, config
from . import auth
from ...core.general.constants import user_active

logging.setLoggerClass(AppLogger)

logger = logging.getLogger(__name__)


@auth.route("/sso_callback")
@sso.require_login
def sso_callback():
    try:
        username = sso.user_getfield(config.SSO_USERNAME_ATTRIBUTE)
        fullname = sso.user_getfield(config.SSO_FULLNAME_ATTRIBUTE)
    except AttributeError:
        logger.error(
            f"Missing 'preferred_username' and / or 'name' in user info; these are required!"
        )
        sso.logout()
        abort(401)

    try:
        resources = sso.access_token_getfield(config.SSO_USERGROUPS_ATTRIBUTE)
    except AttributeError:
        logger.error("Missing resources in OIDC ACCESS token")
        sso.logout()
        abort(401)

    allowed_resources = config.ALLOWED_USER_GROUPS
    allowed_resources.extend(config.ALLOWED_ADMIN_GROUPS)

    user_allowed = False
    admin_allowed = False
    for each in resources:
        if each in allowed_resources:
            if each in config.ALLOWED_ADMIN_GROUPS:
                admin_allowed = True
                break
            user_allowed = True

    if not user_allowed and not admin_allowed:
        logger.info(f"User: {username} is not allowed to login via OIDC....")
        sso.logout()
        abort(401)

    account = db.session.scalar(select(Users).filter(Users.username == username))

    if user_allowed and not admin_allowed:
        # not yet in group; fetching group id
        new_group = db.session.scalar(select(Groups).filter(Groups.name == "user"))
        group_id = new_group.id
    elif admin_allowed:
        # thus admin
        new_group = db.session.scalar(select(Groups).filter(Groups.name == "admin"))
        group_id = new_group.id

    if account:
        # password validation is done by oidc; just log the user in
        account.last_login = int(time.time())

        # set account group membership
        account.group_member[0].group = group_id

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
        new_user.email = f"{username}@display.io"

        # this account is created from openid; generate random password...
        new_user.password = generate_random_password()

        new_user.created = int(time.time())
        new_user.last_login = int(time.time())

        db.session.add(new_user)
        db.session.commit()

        db.session.add(GroupMembers(group=group_id, user=new_user.id))
        db.session.commit()

        login_user(new_user)
        return redirect(url_for("home.index"))
