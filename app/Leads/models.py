import datetime as _dt
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

class Leads(_database.Base):
    __tablename__ = "leads"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    first_name = _sql.Column(_sql.String)
    last_name = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String)
    mobile = _sql.Column(_sql.String)
    phone = _sql.Column(_sql.String)
    staff_id = _sql.Column(_sql.Integer)
    status = _sql.Column(_sql.String)
    source_id = _sql.Column(_sql.Integer)
    lead_since = _sql.Column(_sql.Date)
    notes=_sql.Column(_sql.String,nullable=True)
    created_at= _sql.Column(_sql.DateTime,default=_dt.datetime.now)
    updated_at= _sql.Column(_sql.DateTime,default=_dt.datetime.now)
    created_by= _sql.Column(_sql.Integer)
    updated_by= _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
