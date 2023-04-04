import time

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from display.webapp.run import db


class users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column("username", db.String(128), unique=True)
    password_hash = db.Column("password", db.String(512))
    created = db.Column("created", db.Integer, default=0)
    updated = db.Column("updated", db.Integer, default=0)
    group_member = db.relationship("groupmembers", backref="user", lazy="joined")

    def __repr__(self):
        return f"<< User: {self.username} >>"

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.password_hash = generate_password_hash(password, method="pbkdf2:sha512")

    def verify_password(self, password):
        return check_password_hash(self.password_hash, password)

    def user_to_dict(self):

        user_dict = {
            "id": self.id,
            "username": self.username,
            "groupsmember": self.get_user_groups(),
        }

        return user_dict

    def get_user_groups(self):

        return [x.group.name for x in self.group_member]


class groups(db.Model):
    __tablename__ = "groups"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(256), index=True, unique=True)
    description = db.Column("description", db.String(512))
    members = db.relationship("groupmembers", backref="group", lazy="dynamic")
    created = db.Column("created", db.Integer, default=0)
    updated = db.Column("updated", db.Integer, default=0)

    def __repr__(self):
        return f"<< Group: {self.name} >>"


class groupmembers(db.Model):
    __tablename__ = "groupmembers"
    id = db.Column("id", db.Integer, primary_key=True)
    groupid = db.Column(
        "groupid",
        db.Integer,
        db.ForeignKey("groups.id", ondelete="cascade", onupdate="cascade"),
    )
    userid = db.Column(
        "userid",
        db.Integer,
        db.ForeignKey("users.id", ondelete="cascade", onupdate="cascade"),
    )

    def __repr__(self):
        return f"<< Groupmember: {self.id} >>"


class tracelog(db.Model):
    __tablename__ = "tracelog"
    id = db.Column("id", db.Integer, primary_key=True)
    url = db.Column("url", db.String(512))
    url_hash = db.Column(
        "url_hash",
        db.String(12),
        index=True,
    )
    timestamp = db.Column(
        "timestamp",
        db.Integer,
        default=int(time.time()),
        index=True,
    )
    action = db.Column(
        "action",
        db.Integer,
        default=0,
        index=True,
    )
    user = db.Column("user", db.String(128), default="display")
    result = db.Column("result", db.String(512))
    reason = db.Column("reason", db.String(512))

    def __repr__(self):
        return f"<< Tracelog: {self.id} / {self.url_hash}"
