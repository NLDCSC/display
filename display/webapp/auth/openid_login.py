import random
import time

import requests
from flask import redirect, url_for, abort
from flask_login import login_user

from display.webapp.app.models import users, groups, groupmembers
from display.webapp.run import db, oidc
from . import auth


@auth.route("/oidc_login")
@oidc.require_login
def oidc_login():
    this_client_secrets = oidc.client_secrets

    username = oidc.user_getfield("preferred_username")

    client_roles = oidc.user_getfield("resource_access")

    try:
        client_roles = client_roles[this_client_secrets["client_id"]]["roles"]
    except KeyError:
        oidc_logout()
        abort(401)

    kc_roles = []

    try:
        for each in client_roles:
            kc_roles.append(each)
    except TypeError:
        oidc_logout()
        abort(401)

    if len(kc_roles) == 0:
        oidc_logout()
        abort(401)

    account = users.query.filter_by(username=username).first()

    if account:

        if len(account.group_member) != 0:

            group_names = account.get_user_groups()

            for role in kc_roles:
                # already member of a group; check, alter when needed and save to backend

                if role not in group_names:
                    # not yet in group; fetching group id
                    new_group = groups.query.filter_by(name=role).first()
                    if new_group:
                        # existing group
                        group_id = new_group.id
                    else:
                        # non-existing group
                        new_group = groups(name=role, created=int(time.time()))
                        db.session.add(new_group)
                        db.session.commit()

                        group_id = new_group.id

                    db.session.commit()

        else:
            for role in kc_roles:
                # not yet in group; fetching group id
                new_group = groups.query.filter_by(name=role).first()
                if new_group:
                    # exsting group
                    group_id = new_group.id
                else:
                    # non-existing group
                    new_group = groups(name=role, created=int(time.time()))
                    db.session.add(new_group)
                    db.session.commit()

                    group_id = new_group.id

                db.session.add(groupmembers(groupid=group_id, userid=account.id))
                db.session.commit()

        db.session.add(account)
        db.session.commit()

        # password validation is done by oidc; just log the user in
        login_user(account)
        return redirect(url_for("home.index"))
    else:
        # nobody found; create user account; set keycloak rights and groups and log the user in
        newuser = users()

        newuser.username = username

        # this account is created from openid; generate random password...
        chars = (
            "abcdefghijklmnopqrstuvwxyz"
            "ABCDEFGHIJKLMNOPQRSTUVXYZ"
            "0123456789"
            "#()^[]-_*%&=+/"
        )

        newuser.password = "".join(
            [random.SystemRandom().choice(chars) for _ in range(50)]
        )

        newuser.created = int(time.time())

        db.session.add(newuser)
        db.session.commit()

        for role in kc_roles:

            # not yet in group; fetching group id
            new_group = groups.query.filter_by(name=role).first()
            if new_group:
                # existing group
                group_id = new_group.id
            else:
                # non-existing group
                new_group = groups(name=role, created=int(time.time()))
                db.session.add(new_group)
                db.session.commit()

                group_id = new_group.id

            db.session.add(groupmembers(groupid=group_id, userid=newuser.id))
            db.session.commit()

        login_user(newuser)
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
