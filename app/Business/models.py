import datetime as _dt
from datetime import date
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

class Business(_database.Base):
    __tablename__ = "business"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String)
    address = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String, unique=True)
    owner_id = _sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    date_created = _sql.Column(_sql.Date)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    