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
    username = _sql.Column(_sql.String)
    password = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String, unique=True, index=True)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    org_id = _sql.Column(_sql.Integer, index=True)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
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
