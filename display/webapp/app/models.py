from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from display.webapp.run import db

__all__ = ["users", "groups", "groupmembers"]


class users(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column("username", db.String(48), unique=True)
    password_hash = db.Column("password", db.String(512))
    role = db.Column("role", db.String(16), default="user")
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
            "role": self.role,
        }

        return user_dict


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
