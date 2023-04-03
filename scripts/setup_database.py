import time

from app import app
from display.webapp.app.models import users, groups, groupmembers
from display.webapp.run import db
import secrets
import string


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
]

with app.app_context():

    for each in default_groups:
        print(f"Creating group {each}")
        new_group = groups(name=each["group_name"], description=each["group_description"], created=int(time.time()))
        db.session.add(new_group)

    db.session.commit()

    print("Creating default admin user")

    admin_user = users()
    admin_user.username = "admin"

    admin_password = generate_admin_password()

    print(
        f"Showing admin password one-time-only: {admin_password} \nPlease make a note and store somewhere safe..."
    )

    admin_user.password = admin_password
    admin_user.role = "administrator"
    admin_user.created = int(time.time())

    db.session.add(admin_user)
    db.session.commit()

    admin_group_id = groups.query.filter_by(name="admin").first()

    print("Adding admin user as a groupmember of admin group")
    admin_group = groupmembers()
    admin_group.userid = admin_user.id
    admin_group.groupid = admin_group_id.id

    db.session.add(admin_group)
    db.session.commit()

print("Done!")
