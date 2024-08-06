
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative
from enum import Enum as PyEnum

class Status(PyEnum):
    active='active'
    inactive='inactive'

class Client(_database.Base):
    __tablename__ = "client"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    wallet_address = _sql.Column(_sql.String)
    profile_img = _sql.Column(_sql.String(150))  # varchar(150) in the image is likely a typo
    own_member_id = _sql.Column(_sql.String, nullable=False)
    first_name = _sql.Column(_sql.String, nullable=False)
    last_name = _sql.Column(_sql.String, nullable=False)
    gender = _sql.Column(_sql.String(10))  # varchar(10) in the image is likely the intended length
    dob = _sql.Column(_sql.Date, nullable=False)
    email = _sql.Column(_sql.String, nullable=False)
    phone = _sql.Column(_sql.String(11))  # Assuming phone number should not include landline
    mobile_number = _sql.Column(_sql.String(11))
    notes = _sql.Column(_sql.String)
    source_id= _sql.Column(_sql.Integer)  # Removed foreign key reference
    language = _sql.Column(_sql.String(50))
    is_business = _sql.Column(_sql.Boolean, default=False)
    business_id = _sql.Column(_sql.Integer)
    country_id = _sql.Column(_sql.Integer)  # Removed foreign key reference
    city = _sql.Column(_sql.String(20))
    zipcode = _sql.Column(_sql.String(10))
    address_1 = _sql.Column(_sql.String(100))  # address 1 renamed to address_1 for clarity
    address_2 = _sql.Column(_sql.String(100))
    activated_on = _sql.Column(_sql.Date)
    height= _sql.Column(_sql.Float) 
    weight= _sql.Column(_sql.Float) 
    bmi= _sql.Column(_sql.Float)     
    circumference_waist_navel= _sql.Column(_sql.Float)
    fat_percentage= _sql.Column(_sql.Float)
    muscle_percentage= _sql.Column(_sql.Float)
    check_in = _sql.Column(_sql.DateTime)
    last_online = _sql.Column(_sql.DateTime)
    client_since = _sql.Column(_sql.Date, nullable=False)
    created_at = _sql.Column(_sql.DateTime)
    updated_at = _sql.Column(_sql.DateTime)
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean, default=False)
    

class ClientMembership(_database.Base):
    __tablename__ = "client_membership"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    client_id = _sql.Column(_sql.Integer)
    membership_plan_id = _sql.Column(_sql.Integer)
    prolongation_period = _sql.Column(_sql.Integer)
    auto_renew_days = _sql.Column(_sql.Integer)
    inv_days_cycle = _sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime)
    updated_at = _sql.Column(_sql.DateTime)
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
class ClientOrganization(_database.Base):
    __tablename__ = "client_organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    client_id = _sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    client_status=_sql.Column(_sql.Enum(Status))
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
    
class ClientCoach(_database.Base):
    __tablename__ = "client_coach"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    client_id = _sql.Column(_sql.Integer)
    coach_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
