import datetime as _dt
from datetime import date
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

# Base = _declarative.declarative_base()

class User(_database.Base):
    __tablename__ = "user"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    username = _sql.Column(_sql.String)
    password = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String, unique=True, index=True)
    # otp = _sql.Column(_sql.Integer)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    # is_verified = _sql.Column(_sql.Boolean , default=False)
    # role_id = _sql.Column(_sql.Integer ,index=True)
    org_id = _sql.Column(_sql.Integer, index=True)
    
    def verify_password(self, password: bytes):
        print("In Verify Password", password, self.password.encode('utf-8'))
        return _bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


class Client(_database.Base):
    __tablename__ = "client"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    username = _sql.Column(_sql.String(255), nullable=False)
    wallet_address = _sql.Column(_sql.String(255), nullable=False)
    profile_url=_sql.Column(_sql.String(255))
    own_member_id = _sql.Column(_sql.String(255), nullable=False)
    first_name = _sql.Column(_sql.String(255), nullable=False)
    last_name = _sql.Column(_sql.String(255), nullable=False)
    sex = _sql.Column(_sql.String(255))
    date_of_birth = _sql.Column(_sql.Date, nullable=False)
    email_address = _sql.Column(_sql.String(255), nullable=False, unique=True)
    landline_number = _sql.Column(_sql.String(255))
    mobile_number = _sql.Column(_sql.String(255))
    client_since = _sql.Column(_sql.Date, nullable=False)
    subscription_reason = _sql.Column(_sql.String(255))
    source = _sql.Column(_sql.String(255))
    language = _sql.Column(_sql.String(255))
    is_business = _sql.Column(_sql.Boolean, default=False)
    country = _sql.Column(_sql.String(255))
    city = _sql.Column(_sql.String(255))
    zip_code = _sql.Column(_sql.String(255))
    address = _sql.Column(_sql.String(255))
    bank_detail_id = _sql.Column(_sql.String(255))

class BankAccount(_database.Base):
    __tablename__ = "bank_account"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    bank_account_number = _sql.Column(_sql.String(255), nullable=False)
    bic_swift_code = _sql.Column(_sql.String(255), nullable=False)
    bank_account_holder_name = _sql.Column(_sql.String(255), nullable=False)
    bank_name = _sql.Column(_sql.String(255), nullable=False)


class Organization(_database.Base):
    __tablename__ = "organization"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    org_name = _sql.Column(_sql.String(255), nullable=False)

class Client_Organization(_database.Base):
    __tablename__ = "client_organization"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    client_id = _sql.Column(_sql.Integer, nullable=False)
    org_id = _sql.Column(_sql.Integer, nullable=False)


_database.Base.metadata.create_all(_database.engine)