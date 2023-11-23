import secrets
import string

from app import app
from display.core.general.constants import user_active
from display.webapp.app.models import (
    Users,
    Groups,
    GroupMembers,
    Permissions,
    GroupPermissions,
)
from display.webapp.run import db


def generate_admin_password():
    # define the alphabet
    letters = string.ascii_letters
    digits = string.digits

    alphabet = letters + digits

    # fix password length
    pwd_length = 32

    # generate a password string
    pwd = ""
    for i in range(pwd_length):
        pwd += "".join(secrets.choice(alphabet))

    return pwd


default_groups = [
    {"group_name": "admin", "group_description": "Admin user group"},
    {"group_name": "user", "group_description": "Default user group"},
    {"group_name": "superuser", "group_description": "Super user group"},
]

default_permissions = [
    {"permission_name": "Dashboard", "flask_decorator": "dashboard"},
    {"permission_name": "Logs", "flask_decorator": "logs"},
    {"permission_name": "Users", "flask_decorator": "users"},
    {"permission_name": "Permissions", "flask_decorator": "permissions"},
    {"permission_name": "Api documentation", "flask_decorator": "apidocs"},
]

with app.app_context():
    for each in default_groups:
        print(f"Creating group {each}")
        new_group = Groups(
            name=each["group_name"],
            description=each["group_description"],
        )
        db.session.add(new_group)

    for each in default_permissions:
        print(f"Creating group {each}")
        new_permission = Permissions(
            name=each["permission_name"],
            flask_decorator=each["flask_decorator"],
        )
        db.session.add(new_permission)

    db.session.commit()

    # setting default permission values
    all_groups = (
        Groups.query.filter(~Groups.name.in_(["admin", "superuser"]))
        .order_by(Groups.name)
        .all()
    )
    all_permissions = Permissions.query.order_by(Permissions.id).all()

    for the_group in all_groups:
        for perm in all_permissions:
            new_groupperm = GroupPermissions(
                permission=perm.id, group=the_group.id, value=0
            )
            db.session.add(new_groupperm)
        db.session.commit()

    print("Creating default admin user")

    admin_user = Users()
    admin_user.username = "admin"
    admin_user.email = "admin@certexmon.io"
    admin_user.active = user_active.ENABLED

    admin_password = generate_admin_password()

    print(
        f"Showing admin password one-time-only: {admin_password} \nPlease make a note and store somewhere safe..."
    )

    admin_user.password = admin_password

    db.session.add(admin_user)
    db.session.commit()

    admin_group_id = Groups.query.filter_by(name="admin").first()

    print("Adding admin user as a groupmember of admin group")
    admin_group = GroupMembers()
    admin_group.user = admin_user.id
    admin_group.group = admin_group_id.id

    db.session.add(admin_group)
    db.session.commit()

print("Done!")
