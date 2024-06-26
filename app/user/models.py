import datetime as _dt
from datetime import date
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

# Base = _declarative.declarative_base()

class User(_database.Base):
    __tablename__ = "organization_users"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    username = _sql.Column(_sql.String)
    password = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String, unique=True, index=True)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    org_id = _sql.Column(_sql.Integer, index=True)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
    def verify_password(self, password: bytes):
        print("In Verify Password", password, self.password.encode('utf-8'))
        return _bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

    

class Leads(_database.Base):
    __tablename__ = "leads"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    first_name = _sql.Column(_sql.String)
    last_name = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String)
    mobile_number = _sql.Column(_sql.String)
    home_number = _sql.Column(_sql.String)
    lead_owner = _sql.Column(_sql.String)
    status = _sql.Column(_sql.String)
    source = _sql.Column(_sql.String)
    lead_since = _sql.Column(_sql.Date)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
class BankAccount(_database.Base):
    __tablename__ = "bank_account"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    bank_account_number = _sql.Column(_sql.String, nullable=False)
    bic_swift_code = _sql.Column(_sql.String, nullable=False)
    bank_account_holder_name = _sql.Column(_sql.String, nullable=False)
    bank_name = _sql.Column(_sql.String, nullable=False)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

class Organization(_database.Base):
    __tablename__ = "organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    org_name = _sql.Column(_sql.String, nullable=False)
    is_deleted= _sql.Column(_sql.Boolean, default=False)


_database.Base.metadata.create_all(_database.engine)