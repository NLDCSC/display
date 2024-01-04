import collections
import hashlib
import uuid
from html import escape

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash

from display.core.general.constants import user_permissions
from display.webapp.helpers.utils.times import timestampTOdatetimestring
from display.webapp.run import db


class AppDefaultModel(db.Model):
    __abstract__ = True


class Users(UserMixin, AppDefaultModel):
    __tablename__ = "users"
    id = db.Column("id", db.Integer, primary_key=True)
    username = db.Column("username", db.String(30), index=True, unique=True)
    fullname = db.Column("fullname", db.String(128), default="NA")
    email = db.Column("email", db.String(256), index=True, unique=True)
    pw_hash = db.Column("pw_hash", db.String(512))
    active = db.Column("active", db.Integer, default=0)
    api_key = db.Column("api_key", db.String(512))
    api_key_lookup = db.Column("api_key_lookup", db.String(128))
    last_login = db.Column("last_login", db.Integer, default=0)
    approval = db.Column("approval", db.Integer, default=0)
    system = db.Column("system", db.Integer, default=0)

    # ORM CLASS MAPPINGS
    group_member = db.relationship(
        "GroupMembers", back_populates="users", lazy="joined"
    )

    def __repr__(self):
        return f"<< Users: {self.id} >>"

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password):
        self.pw_hash = generate_password_hash(
            password, method="pbkdf2:sha512", salt_length=128
        )

    @property
    def apikey(self):
        raise AttributeError("apikey is not a readable attribute")

    @apikey.setter
    def apikey(self, api_key):
        self.api_key = generate_password_hash(
            api_key, method="pbkdf2:sha512", salt_length=128
        )

    def verify_password(self, password):
        return check_password_hash(self.pw_hash, password)

    def verify_api_key(self, api_key):
        return check_password_hash(self.api_key, api_key)

    def user_to_dict(self):
        user_dict = {
            "id": self.id,
            "username": escape(self.username),
            "fullname": escape(self.fullname),
            "email": escape(self.email),
            "groupsmember": self.get_user_groups(),
            "status": self.active,
            "approval": self.approval,
            "system": self.system,
            "got_key": self.has_api_key(),
            "last_login": timestampTOdatetimestring(self.last_login, True),
        }

        return user_dict

    def has_api_key(self):
        if self.api_key is not None:
            return True

        return False

    def get_user_groups(self):
        return [x.groups.name for x in self.group_member]

    def is_admin(self):
        if "admin" not in self.get_user_groups():
            return False

        return True

    def is_superuser(self):
        if "superuser" not in self.get_user_groups():
            return False

        return True

    def can_approve(self):
        if self.approval == 1 or self.is_admin() or self.is_superuser():
            return True

        return False

    def is_system(self):
        if self.system == 1:
            return True

        return False

    def check_in_group(self, groupname):
        if groupname not in self.get_user_groups():
            return False

        return True

    def get_user_group(self):
        return self.get_user_groups()[0]

    def get_user_group_object(self):
        return self.group_member[0].groups

    def get_group_permissions_by_permission_id(self, the_id):
        return int(
            self.get_user_group_object().get_group_permission_by_permission_id(the_id)
        )

    def group_is_allowed(self, groups: list):
        if (
            self.get_user_group() not in groups
            and not self.is_admin()
            and not self.is_superuser()
        ):
            return False

        return True

    def parse_permissions(self):
        perms = sorted(
            self.get_user_group_object().permissions, key=lambda x: x.permission
        )

        ret_dict = collections.defaultdict(int)

        for each in perms:
            ret_dict[each.permissions.flask_decorator] = each.value

        return dict(ret_dict)

    def get_permission_by_decorator(self, decorator: str):
        if self.is_admin():
            return user_permissions.WRITE

        try:
            return self.parse_permissions()[decorator]
        except KeyError:
            return user_permissions.NONE

    def is_active(self):
        if self.active != 1:
            return False

        return True

    def create_api_key(self):
        random_uuid = uuid.uuid4()

        key = hashlib.md5(str(random_uuid).encode("utf-8")).hexdigest()

        self.api_key_lookup = key[:8]

        return key


class Groups(AppDefaultModel):
    __tablename__ = "groups"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(256), index=True, unique=True)
    description = db.Column("description", db.String(512))

    # ORM CLASS MAPPINGS
    groupmembers = db.relationship(
        "GroupMembers", back_populates="groups", lazy="joined"
    )
    permissions = db.relationship(
        "GroupPermissions", back_populates="groups", lazy="joined"
    )

    def get_group_permission_by_permission_id(self, the_id):
        value = [x.value for x in self.permissions if x.permission == the_id]

        if len(value) > 0:
            return value[0]
        else:
            return "NA"

    def __repr__(self):
        return f"<< Groups: {self.name} >>"


class Permissions(AppDefaultModel):
    __tablename__ = "permissions"
    id = db.Column("id", db.Integer, primary_key=True)
    name = db.Column("name", db.String(256), index=True, unique=True)
    flask_decorator = db.Column("flask_decorator", db.String(100), unique=True)

    # ORM CLASS MAPPINGS
    permission_member = db.relationship(
        "GroupPermissions", back_populates="permissions", lazy="joined"
    )

    def get_sorted_group_permissions(self):
        return sorted(self.permission_member, key=lambda x: x.groups.name)

    def __repr__(self):
        return f"<< Permissions: {self.id} >>"


class GroupPermissions(AppDefaultModel):
    __tablename__ = "grouppermissions"
    id = db.Column("id", db.Integer, primary_key=True)
    permission = db.Column(
        "permission",
        db.Integer,
        db.ForeignKey("permissions.id", ondelete="cascade", onupdate="cascade"),
    )
    group = db.Column(
        "group",
        db.Integer,
        db.ForeignKey("groups.id", ondelete="cascade", onupdate="cascade"),
    )
    # 0 = none, 1 = read, 2 = write
    value = db.Column("value", db.Integer, default=0, index=True)

    # ORM CLASS MAPPINGS
    permissions = db.relationship(
        "Permissions", back_populates="permission_member", lazy="joined"
    )
    groups = db.relationship("Groups", back_populates="permissions", lazy="joined")

    def __repr__(self):
        return f"<< GroupPermissions: {self.id} >>"


class GroupMembers(AppDefaultModel):
    __tablename__ = "groupmembers"
    id = db.Column("id", db.Integer, primary_key=True)
    group = db.Column(
        "group",
        db.Integer,
        db.ForeignKey("groups.id", ondelete="cascade", onupdate="cascade"),
    )
    user = db.Column(
        "user",
        db.Integer,
        db.ForeignKey("users.id", ondelete="cascade", onupdate="cascade"),
    )

    # ORM CLASS MAPPINGS
    users = db.relationship("Users", back_populates="group_member", lazy="joined")
    groups = db.relationship("Groups", back_populates="groupmembers", lazy="joined")

    def __repr__(self):
        return f"<< GroupMembers: {self.id} >>"


class Tracelog(AppDefaultModel):
    __tablename__ = "tracelog"
    id = db.Column("id", db.Integer, primary_key=True)
    url = db.Column("url", db.String(512))
    hash = db.Column(
        "hash",
        db.String(12),
        index=True,
    )
    timestamp = db.Column(
        "timestamp",
        db.Integer,
        default=0,
        index=True,
    )
    action = db.Column(
        "action",
        db.String(25),
        index=True,
    )
    user = db.Column("user", db.String(128), default="display")
    result = db.Column(
        "result",
        db.String(25),
        index=True,
    )
    status_code = db.Column(
        "status_code",
        db.Integer,
        default=0,
        index=True,
    )
    reason = db.Column("reason", db.String(512))

    def to_data_dict(self):
        return {
            "url": self.url,
            "hash": self.hash,
            "timestamp": timestampTOdatetimestring(self.timestamp, True),
            "action": self.action,
            "user": self.user,
            "result": self.result,
            "status_code": self.status_code,
            "reason": self.reason,
        }

    def __repr__(self):
        return f"<< Tracelog: {self.id} / {self.url_hash} >>"
