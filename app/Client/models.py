
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

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
    
    
class ClientCoach(_database.Base):
    __tablename__ = "client_coach"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    client_id = _sql.Column(_sql.Integer)
    coach_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)


_database.Base.metadata.create_all(_database.engine)