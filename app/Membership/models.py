import datetime as _dt
from datetime import date
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

class MembershipPlan(_database.Base):
    __tablename__ = "membership_plan"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String)
    price = _sql.Column(_sql.String)  
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    created_at=_sql.Column(_sql.DateTime)
    updated_at=_sql.Column(_sql.DateTime)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    
    
class UserMembership(_database.Base):
    __tablename__ = "user_membership"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer)
    membership_plan_id = _sql.Column(_sql.Integer)
    start_date = _sql.Column(_sql.Date)
    end_date = _sql.Column(_sql.Date)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
class Membership_group(_database.Base):
    __tablename__ = "membership_group"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String)
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    created_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    updated_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    
class Credits(_database.Base):
    __tablename__ = "credits"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String)
    min_limit=_sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    created_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    updated_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)

class Income_category(_database.Base):
    __tablename__ = "income_category"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String)
    position=_sql.Column(_sql.Integer)
    sale_tax_id=_sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    created_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    updated_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    
class Sale_tax(_database.Base):
    __tablename__ = "sale_tax"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String)
    percentage=_sql.Column(_sql.Float)
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    created_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    updated_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
      
