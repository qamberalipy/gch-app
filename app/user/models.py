import datetime as _dt
from datetime import date
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

    
class User(_database.Base):
    __tablename__ = "staff"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    profile_img = _sql.Column(_sql.String(150))
    password = _sql.Column(_sql.String(100))
    first_name = _sql.Column(_sql.String(50))
    last_name = _sql.Column(_sql.String(50))
    gender = _sql.Column(_sql.String(10))
    dob = _sql.Column(_sql.DateTime)
    email = _sql.Column(_sql.String(100), unique=True, index=True)
    phone = _sql.Column(_sql.String(11))
    mobile = _sql.Column(_sql.String(11))
    notes = _sql.Column(_sql.String)
    source_id = _sql.Column(_sql.Integer)
    org_id =_sql.Column(_sql.Integer)
    role_id = _sql.Column(_sql.Integer)
    country_id = _sql.Column(_sql.Integer)
    city = _sql.Column(_sql.String(20))
    zipcode = _sql.Column(_sql.String)
    address_1 = _sql.Column(_sql.String(100))
    address_2 = _sql.Column(_sql.String)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now)
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now)
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean, default=False)
    
    def verify_password(self, password: bytes):
        print("In Verify Password", password, self.password.encode('utf-8'))
        return _bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))

class Country(_database.Base):
    __tablename__ = "country"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    country = _sql.Column(_sql.String)
    country_code = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
class Source(_database.Base):
    __tablename__ = "source"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    source = _sql.Column(_sql.String)
    

class Organization(_database.Base):
    __tablename__ = "organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    org_name = _sql.Column(_sql.String, nullable=False)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

class Role(_database.Base):
    __tablename__ = "role"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name=_sql.Column(_sql.String(50))
    is_deleted=_sql.Column(_sql.Boolean)

class Resource(_database.Base):
    __tablename__ = "resource"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name=_sql.Column(_sql.String(50))
    code=_sql.Column(_sql.String(50))
    parent=_sql.Column(_sql.String(50))
    is_parent=_sql.Column(_sql.Boolean)
    is_deleted=_sql.Column(_sql.Boolean)

class Permission(_database.Base):
    __tablename__ = 'permission'
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    role_id= _sql.Column(_sql.Integer)
    resource_id= _sql.column(_sql.Integer)
    access= _sql.Column(_sql.String(50))
    is_deleted=_sql.Column(_sql.Boolean)

    
class Transaction(_database.Base):
    __tablename__ = 'transaction'

    id = _sql.Column(_sql.Integer, primary_key=True, server_default=_sql.text("nextval('transaction_id_seq'::regclass)"), autoincrement=True)
    transaction_hash = _sql.Column(_sql.String, unique=True)
    _from = _sql.Column('from', _sql.String)
    to = _sql.Column(_sql.String)
    value = _sql.Column(_sql.String)
    event_type = _sql.Column(_sql.String)
    status = _sql.Column(_sql.Enum('pending', 'success', 'failed', name='TransactionEnums'), nullable=False, server_default=_sql.text("'pending'::\"TransactionEnums\""))
    created_at = _sql.Column(_sql.TIMESTAMP, nullable=False, server_default=_sql.text("CURRENT_TIMESTAMP"))
    updated_at = _sql.Column(_sql.TIMESTAMP, nullable=False, server_default=_sql.text("CURRENT_TIMESTAMP"))