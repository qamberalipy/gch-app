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
    org_id = _sql.Column(_sql.Integer)
    group_id = _sql.Column(_sql.Integer)
    status = _sql.Column(_sql.String(10))  
    description = _sql.Column(_sql.Text)  
    access_time = _sql.Column(_sql.JSON)
    net_price = _sql.Column(_sql.Float)
    income_category_id = _sql.Column(_sql.Integer)
    discount = _sql.Column(_sql.Float)
    total_price = _sql.Column(_sql.Float)
    payment_method = _sql.Column(_sql.String(20))  # varchar(20) in the image description
    reg_fee = _sql.Column(_sql.Float)
    billing_cycle = _sql.Column(_sql.String(30))  # varchar(30) in the image description
    auto_renewal = _sql.Column(_sql.Boolean, default=False)
    renewal_details = _sql.Column(_sql.JSON)
    credit_id = _sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now)
    updated_at = _sql.Column(_sql.DateTime,default=_dt.datetime.now)
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean, default=False)
    
    
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
    created_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    updated_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
class Facility(_database.Base):
    __tablename__ = "facility"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String)
    min_limit=_sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    status=_sql.Column(_sql.Boolean,default=True)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    created_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    updated_at=_sql.Column(_sql.DateTime,default=_dt.datetime.now)
    created_by=_sql.Column(_sql.Integer)
    updated_by=_sql.Column(_sql.Integer)
    
class Facility_membership_plan(_database.Base):
    __tablename__ = "facility_membership_plan"
    
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    facility_id=_sql.Column(_sql.Integer)
    membership_plan_id=_sql.Column(_sql.Integer)
    total_credits = _sql.Column(_sql.Integer)
    validity = _sql.Column(_sql.JSON)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
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
      
