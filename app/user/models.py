import datetime as _dt
from enum import Enum as _PyEnum
import sqlalchemy as _sql
from sqlalchemy.sql import func
import app.core.db.session as _database
from passlib.context import CryptContext

pwd_ctx = CryptContext(schemes=["bcrypt"], deprecated="auto")

# --- Enums ---

class UserRole(str, _PyEnum):
    admin = "admin"
    manager = "manager"
    team_member = "team_member"
    digital_creator = "digital_creator"

class AccountStatus(str, _PyEnum):
    active = "active"
    suspended = "suspended"
    deleted = "deleted"

class Gender(str, _PyEnum):
    male = "Male"
    female = "Female"
    other = "Other"

# --- Models ---

class User(_database.Base):
    __tablename__ = "user"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    username = _sql.Column(_sql.String(50), unique=True, nullable=True, index=True)
    email = _sql.Column(_sql.String(100), unique=True, nullable=False, index=True)
    full_name = _sql.Column(_sql.String(100), nullable=True)
    profile_picture_url = _sql.Column(_sql.String(255), nullable=True)
    bio = _sql.Column(_sql.Text, nullable=True)
    password_hash = _sql.Column(_sql.String(255), nullable=True)
    
    # Enums
    role = _sql.Column(_sql.Enum(UserRole, name="user_role"), default=UserRole.digital_creator, nullable=False)
    account_status = _sql.Column(_sql.Enum(AccountStatus, name="account_status"), default=AccountStatus.active, nullable=False)
    
    # Contact & Location
    phone = _sql.Column(_sql.String(20), nullable=True)
    mobile_number = _sql.Column(_sql.String(20), nullable=True)
    country_id = _sql.Column(_sql.Integer, nullable=True)
    city = _sql.Column(_sql.String(50), nullable=True)
    zipcode = _sql.Column(_sql.String(20), nullable=True)
    address_1 = _sql.Column(_sql.String(255), nullable=True)
    address_2 = _sql.Column(_sql.String(255), nullable=True)
    timezone = _sql.Column(_sql.String(50), nullable=True)
    
    # Demographics
    gender = _sql.Column(_sql.Enum(Gender, name="gender_enum"), nullable=True) # Added Missing Column
    dob = _sql.Column(_sql.Date, nullable=True)

    # Status Flags
    is_onboarded = _sql.Column(_sql.Boolean, default=False, nullable=False)
    is_deleted = _sql.Column(_sql.Boolean, default=False, nullable=False)

    # Timestamps
    last_checkin = _sql.Column(_sql.DateTime, nullable=True)
    last_online = _sql.Column(_sql.DateTime, nullable=True)
    last_login = _sql.Column(_sql.DateTime, nullable=True)
    created_by = _sql.Column(_sql.Integer, nullable=True)
    updated_at_by = _sql.Column(_sql.Integer, nullable=True)
    created_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = _sql.Column(_sql.DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False)


    def set_password(self, password: str) -> None:
        try:
            safe_pass = password[:72]
            self.password_hash = pwd_ctx.hash(safe_pass)
        except Exception as e:
            raise e

    def verify_password(self, plain_password: str) -> bool:
        try:
            return pwd_ctx.verify(plain_password[:72], self.password_hash)
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
    name = _sql.Column(_sql.String(100), nullable=False)
    is_active = _sql.Column(_sql.Boolean, default=True)


class OTP(_database.Base):
   
    __tablename__ = "otp"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    email = _sql.Column(_sql.String(100), index=True, nullable=False)
    otp = _sql.Column(_sql.String(10), nullable=False)
    purpose = _sql.Column(_sql.String(20), default="verify") # 'verify', 'reset'
    used = _sql.Column(_sql.Boolean, default=False)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)


class RefreshToken(_database.Base):
    __tablename__ = "auth_refresh_tokens"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer, nullable=False)
    token = _sql.Column(_sql.Text, nullable=False)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    revoked = _sql.Column(_sql.Boolean, default=False)