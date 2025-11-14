# app/user/models.py
import datetime as _dt
from enum import Enum as _PyEnum
import sqlalchemy as _sql
from sqlalchemy.sql import func
import app.core.db.session as _database
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")


class RoleStatus(str, _PyEnum):
    active = "active"
    inactive = "inactive"


class AccountStatus(str, _PyEnum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"


class AuthProvider(str, _PyEnum):
    local = "local"
    google = "google"


class User(_database.Base):
    __tablename__ = "user"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)

    # identity & profile
    username = _sql.Column(_sql.String(50), unique=True, nullable=True, index=True)
    email = _sql.Column(_sql.String(100), unique=True, nullable=False, index=True)
    full_name = _sql.Column(_sql.String(100), nullable=True)
    profile_picture_url = _sql.Column(_sql.String(255), nullable=True)
    bio = _sql.Column(_sql.Text, nullable=True)

    # authentication & oauth
    password_hash = _sql.Column(_sql.String(255), nullable=True)
    auth_provider = _sql.Column(_sql.Enum(AuthProvider, name="auth_provider"), nullable=False, default=AuthProvider.local)
    google_id = _sql.Column(_sql.String(255), nullable=True)
    is_verified = _sql.Column(_sql.Boolean, default=False, nullable=False)

    # status & role
    account_status = _sql.Column(_sql.Enum(AccountStatus, name="account_status"), default=AccountStatus.active, nullable=False)
    profile_type_id = _sql.Column(_sql.Integer, nullable=True)

    # contact & address
    phone = _sql.Column(_sql.String(20), nullable=True)
    mobile_number = _sql.Column(_sql.String(20), nullable=True)
    country_id = _sql.Column(_sql.Integer, nullable=True)
    city = _sql.Column(_sql.String(50), nullable=True)
    zipcode = _sql.Column(_sql.String(20), nullable=True)
    address_1 = _sql.Column(_sql.String(255), nullable=True)
    address_2 = _sql.Column(_sql.String(255), nullable=True)

    # activity & metadata
    dob = _sql.Column(_sql.Date, nullable=True)
    last_checkin = _sql.Column(_sql.DateTime, nullable=True)
    last_online = _sql.Column(_sql.DateTime, nullable=True)
    last_login = _sql.Column(_sql.DateTime, nullable=True)

    # subscription / customization
    plan_type_id = _sql.Column(_sql.Integer, nullable=False, default=1)
    theme_id = _sql.Column(_sql.Integer, nullable=True)
    custom_domain = _sql.Column(_sql.String(255), nullable=True)

    # auditing timestamps
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # soft delete
    is_deleted = _sql.Column(_sql.Boolean, default=False, nullable=False)

    # password helpers (uses passlib)
    def set_password(self, password: str) -> None:
        self.password_hash = pwd_ctx.hash(password)

    def verify_password(self, plain_password: str) -> bool:
        if not self.password_hash:
            return False
        try:
            return pwd_ctx.verify(plain_password, self.password_hash)
        except Exception:
            return False


class Country(_database.Base):
    __tablename__ = "country"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    country = _sql.Column(_sql.String(100), nullable=False)
    country_code = _sql.Column(_sql.String(10), nullable=True)
    is_deleted = _sql.Column(_sql.Boolean, default=False, nullable=False)


class Source(_database.Base):
    __tablename__ = "source"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    source = _sql.Column(_sql.String(150), nullable=False)


class ProfileType(_database.Base):
    __tablename__ = "profile_type"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String(50), nullable=False)
    is_deleted = _sql.Column(_sql.Boolean, default=False, nullable=False)


class PlanType(_database.Base):
    __tablename__ = "plan_type"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String(50), nullable=False)
    is_deleted = _sql.Column(_sql.Boolean, default=False, nullable=False)


class OTP(_database.Base):
    __tablename__ = "auth_otps"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    email = _sql.Column(_sql.String(255), index=True, nullable=False)
    otp = _sql.Column(_sql.String(32), nullable=False)
    purpose = _sql.Column(_sql.String(50), nullable=True)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    used = _sql.Column(_sql.Boolean, default=False)


class RefreshToken(_database.Base):
    __tablename__ = "auth_refresh_tokens"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer, nullable=False)
    token = _sql.Column(_sql.Text, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    revoked = _sql.Column(_sql.Boolean, default=False)
