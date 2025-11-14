import datetime as _dt
from enum import Enum as PyEnum
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
from sqlalchemy.sql import func
import app.core.db.session as _database
import bcrypt as _bcrypt

class RoleStatus(str, PyEnum):
    active = "active"
    inactive = "inactive"

class AccountStatus(str, PyEnum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"


class AuthProvider(str, PyEnum):
    local = "local"
    google = "google"

class User(_database.Base):
    __tablename__ = "user"  # kept same name as your original; change to 'users' if preferred

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)

    # identity & profile
    username = _sql.Column(_sql.String(50), unique=True, nullable=True, index=True)  # optional public handle
    email = _sql.Column(_sql.String(100), unique=True, nullable=False, index=True)
    full_name = _sql.Column(_sql.String(100), nullable=True)
    profile_picture_url = _sql.Column(_sql.String(255), nullable=True)  # renamed from profile_img
    bio = _sql.Column(_sql.Text, nullable=True)

    # authentication & oauth
    password_hash = _sql.Column(_sql.String(255), nullable=True)  # nullable for OAuth users
    auth_provider = _sql.Column(_sql.Enum(AuthProvider, name="auth_provider"), nullable=False, default=AuthProvider.local)
    google_id = _sql.Column(_sql.String(255), nullable=True)  # store Google 'sub' if using Google OAuth
    is_verified = _sql.Column(_sql.Boolean, default=False, nullable=False)  # email verified flag

    # status & role
    account_status = _sql.Column(_sql.Enum(AccountStatus, name="account_status"), default=AccountStatus.active, nullable=False)
    profile_type_id = _sql.Column(_sql.Integer, nullable=True)

    # contact & address
    phone = _sql.Column(_sql.String(20), nullable=True)          # general phone
    mobile_number = _sql.Column(_sql.String(20), nullable=True)  # mobile
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
    plan_type_id = _sql.Column(_sql.Integer, nullable=False, default=1)  # default to 'free' plan
    theme_id = _sql.Column(_sql.Integer, nullable=True)
    custom_domain = _sql.Column(_sql.String(255), nullable=True)

    # auditing timestamps (use DB/server defaults so they update correctly)
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)

    # soft delete
    is_deleted = _sql.Column(_sql.Boolean, default=False, nullable=False)

    # simple helper for password verification
    def verify_password(self, plain_password: str) -> bool:
        """Verify plain password against stored password_hash. Returns False if no password stored."""
        if not self.password_hash:
            return False
        try:
            return _bcrypt.checkpw(plain_password.encode("utf-8"), self.password_hash.encode("utf-8"))
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

class Profile_type(_database.Base):
    __tablename__ = "profile_type"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String(50), nullable=False)
    is_deleted = _sql.Column(_sql.Boolean, default=False, nullable=False)

class Plan_type(_database.Base):
    __tablename__ = "plan_type"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String(50), nullable=False)
    is_deleted = _sql.Column(_sql.Boolean, default=False, nullable=False)

class OTP(_database.Base):
    __tablename__ = "auth_otps"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    email = _sql.Column(_sql.String(255), index=True, nullable=False)
    otp = _sql.Column(_sql.String(32), nullable=False)
    purpose = _sql.Column(_sql.String(50), nullable=True)  # e.g. verify, reset
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    used = _sql.Column(_sql.Boolean, default=False)

class RefreshToken(_database.Base):
    __tablename__ = "auth_refresh_tokens"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer, nullable=False)
    token = _sql.Column(_sql.Text, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    revoked = _sql.Column(_sql.Boolean, default=False)