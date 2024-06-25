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

class Client(_database.Base):
    __tablename__ = "client"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    wallet_address = _sql.Column(_sql.String)
    profile_url=_sql.Column(_sql.String)
    own_member_id = _sql.Column(_sql.String, nullable=False)
    first_name = _sql.Column(_sql.String, nullable=False)
    last_name = _sql.Column(_sql.String, nullable=False)
    sex = _sql.Column(_sql.String)
    date_of_birth = _sql.Column(_sql.Date, nullable=False)
    email_address = _sql.Column(_sql.String, nullable=False, unique=True)
    landline_number = _sql.Column(_sql.String)
    mobile_number = _sql.Column(_sql.String)
    client_since = _sql.Column(_sql.Date, nullable=False)
    notes = _sql.Column(_sql.String)
    source = _sql.Column(_sql.String)
    language = _sql.Column(_sql.String)
    is_business = _sql.Column(_sql.Boolean, default=False)
    business_id = _sql.Column(_sql.Integer)
    country = _sql.Column(_sql.String)
    city = _sql.Column(_sql.String)
    zip_code = _sql.Column(_sql.String)
    address = _sql.Column(_sql.String)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

class MembershipPlan(_database.Base):
    __tablename__ = "membership_plan"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    name = _sql.Column(_sql.String)
    price = _sql.Column(_sql.String)  
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

class ClientMembership(_database.Base):
    __tablename__ = "client_membership"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    client_id = _sql.Column(_sql.Integer)
    membership_plan_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
class ClientOrganization(_database.Base):
    __tablename__ = "client_organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    client_id = _sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

class UserMembership(_database.Base):
    __tablename__ = "user_membership"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer)
    membership_plan_id = _sql.Column(_sql.Integer)
    start_date = _sql.Column(_sql.Date)
    end_date = _sql.Column(_sql.Date)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
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

class Coach(_database.Base):
    __tablename__ = "coach"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    coach_name = _sql.Column(_sql.String)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

class ClientCoach(_database.Base):
    __tablename__ = "client_coach"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    client_id = _sql.Column(_sql.Integer)
    coach_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

class CoachOrganization(_database.Base):
    __tablename__ = "coach_organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    coach_id = _sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

_database.Base.metadata.create_all(_database.engine)