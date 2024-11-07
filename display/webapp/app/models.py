import collections
import hashlib
import uuid as api_key_generator
from html import escape
from typing import Optional, Any

from flask_login import UserMixin
from nldcsc.flask_plugins.flask_sqlalchemy import (
    int_pk,
    str_512,
    str_128,
    str_256,
    str_100,
    big_int_pk,
    str_30,
)
from sqlalchemy import ForeignKey
from sqlalchemy.orm import Mapped, mapped_column, relationship
from werkzeug.security import generate_password_hash, check_password_hash

from display.core.general.constants import user_permissions
from display.webapp.helpers.utils.times import timestampTOdatetimestring
from display.webapp.run import db


class ModelDefault(db.Model):
    __abstract__ = True


class Users(UserMixin, ModelDefault):
    __tablename__ = "users"
    id: Mapped[int_pk]
    username: Mapped[str_128] = mapped_column(index=True, unique=True)
    fullname: Mapped[str_128] = mapped_column(default="NA")
    email: Mapped[str_256] = mapped_column(index=True, unique=True)
    pw_hash: Mapped[str_512]
    active: Mapped[int] = mapped_column(default=0)
    api_key: Mapped[Optional[str_512]]
    api_key_lookup: Mapped[Optional[str_128]]
    last_login: Mapped[int] = mapped_column(default=0)
    approval: Mapped[int] = mapped_column(default=0)
    system: Mapped[int] = mapped_column(default=0)

    # ORM CLASS MAPPINGS
    group_member: Mapped[list["GroupMembers"]] = relationship(
        back_populates="users", lazy="joined"
    )

    def __repr__(self) -> str:
        return f"<< Users: {self.id} >>"

    @property
    def password(self):
        raise AttributeError("password is not a readable attribute")

    @password.setter
    def password(self, password) -> None:
        self.pw_hash = generate_password_hash(
            password, method="pbkdf2:sha512", salt_length=128
        )

    @property
    def apikey(self):
        raise AttributeError("apikey is not a readable attribute")

    @apikey.setter
    def apikey(self, api_key) -> None:
        self.api_key = generate_password_hash(
            api_key, method="pbkdf2:sha512", salt_length=128
        )

    def verify_password(self, password) -> bool:
        return check_password_hash(self.pw_hash, password)

    def verify_api_key(self, api_key) -> bool:
        return check_password_hash(self.api_key, api_key)

    def user_to_dict(self) -> dict[str, Any]:
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

    def has_api_key(self) -> bool:
        if self.api_key is not None:
            return True

        return False

    def get_user_groups(self) -> list:
        return [x.groups.name for x in self.group_member]

    def is_admin(self) -> bool:
        if "admin" not in self.get_user_groups():
            return False

        return True

    def is_superuser(self) -> bool:
        if "superuser" not in self.get_user_groups():
            return False

        return True

    def can_approve(self) -> bool:
        if self.approval == 1 or self.is_admin() or self.is_superuser():
            return True

        return False

    def is_system(self) -> bool:
        if self.system == 1:
            return True

        return False

    def check_in_group(self, groupname) -> bool:
        if groupname not in self.get_user_groups():
            return False

        return True

    def get_user_group(self) -> list:
        return self.get_user_groups()[0]

    def get_user_group_object(self) -> "Groups":
        return self.group_member[0].groups

    def get_group_permissions_by_permission_id(self, the_id) -> int:
        return int(
            self.get_user_group_object().get_group_permission_by_permission_id(the_id)
        )

    def group_is_allowed(self, groups: list) -> bool:
        if (
            self.get_user_group() not in groups
            and not self.is_admin()
            and not self.is_superuser()
        ):
            return False

        return True

    def parse_permissions(self) -> dict[str, int]:
        perms = sorted(
            self.get_user_group_object().permissions, key=lambda x: x.permission
        )

        ret_dict = collections.defaultdict(int)

        for each in perms:
            ret_dict[each.permissions.flask_decorator] = each.value

        return dict(ret_dict)

    def get_permission_by_decorator(self, decorator: str) -> int:
        if self.is_admin():
            return user_permissions.WRITE

        try:
            return self.parse_permissions()[decorator]
        except KeyError:
            return user_permissions.NONE

    def is_active(self) -> bool:
        if self.active != 1:
            return False

        return True

    def create_api_key(self) -> str:
        random_uuid = api_key_generator.uuid4()

        # noinspection InsecureHash
        key = hashlib.md5(str(random_uuid).encode("utf-8")).hexdigest()

        self.api_key_lookup = key[:8]

        return key


class Groups(ModelDefault):
    __tablename__ = "groups"
    id: Mapped[int_pk]
    name: Mapped[str_256] = mapped_column(index=True, unique=True)
    description: Mapped[str_512]

    # ORM CLASS MAPPINGS
    groupmembers: Mapped[list["GroupMembers"]] = relationship(
        back_populates="groups", lazy="joined"
    )
    permissions: Mapped[list["GroupPermissions"]] = relationship(
        back_populates="groups", lazy="joined"
    )

    def get_group_permission_by_permission_id(self, the_id):
        value = [x.value for x in self.permissions if x.permission == the_id]

        if len(value) > 0:
            return value[0]
        else:
            return "NA"

    def __repr__(self):
        return f"<< Groups: {self.name} >>"


class Permissions(ModelDefault):
    __tablename__ = "permissions"
    id: Mapped[int_pk]
    name: Mapped[str_256] = mapped_column(index=True, unique=True)
    flask_decorator: Mapped[str_100] = mapped_column(unique=True)

    # ORM CLASS MAPPINGS
    permission_member: Mapped[list["GroupPermissions"]] = relationship(
        back_populates="permissions", lazy="joined"
    )

    def get_sorted_group_permissions(self):
        return sorted(self.permission_member, key=lambda x: x.groups.name)

    def __repr__(self):
        return f"<< Permissions: {self.id} >>"


class GroupPermissions(ModelDefault):
    __tablename__ = "grouppermissions"
    id: Mapped[int_pk]
    permission: Mapped[int] = mapped_column(
        ForeignKey("permissions.id", ondelete="cascade", onupdate="cascade"),
    )
    group: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="cascade", onupdate="cascade"),
    )
    # 0 = none, 1 = read, 2 = write
    value: Mapped[int] = mapped_column(default=0, index=True)

    # ORM CLASS MAPPINGS
    permissions: Mapped[Permissions] = relationship(
        back_populates="permission_member", lazy="joined"
    )
    groups: Mapped[Groups] = relationship(back_populates="permissions", lazy="joined")

    def __repr__(self):
        return f"<< GroupPermissions: {self.id} >>"


class GroupMembers(ModelDefault):
    __tablename__ = "groupmembers"
    id: Mapped[int_pk]
    group: Mapped[int] = mapped_column(
        ForeignKey("groups.id", ondelete="cascade", onupdate="cascade"),
    )
    user: Mapped[int] = mapped_column(
        ForeignKey("users.id", ondelete="cascade", onupdate="cascade"),
    )

    # ORM CLASS MAPPINGS
    users: Mapped[Users] = relationship(back_populates="group_member", lazy="joined")
    groups: Mapped[Groups] = relationship(back_populates="groupmembers", lazy="joined")

    def __repr__(self):
        return f"<< GroupMembers: {self.id} >>"


class Tracelog(ModelDefault):
    __tablename__ = "tracelog"
    id: Mapped[big_int_pk]
    url: Mapped[str_512]
    hash: Mapped[str_30] = mapped_column(index=True)
    timestamp: Mapped[int] = mapped_column(default=0, index=True)
    action: Mapped[str_30] = mapped_column(index=True)
    user: Mapped[str_128] = mapped_column(default="display")
    result: Mapped[str_30] = mapped_column(index=True)
    status_code: Mapped[int] = mapped_column(default=0, index=True)
    reason: Mapped[str_512]

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
