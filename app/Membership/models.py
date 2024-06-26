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
    
class UserMembership(_database.Base):
    __tablename__ = "user_membership"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    user_id = _sql.Column(_sql.Integer)
    membership_plan_id = _sql.Column(_sql.Integer)
    start_date = _sql.Column(_sql.Date)
    end_date = _sql.Column(_sql.Date)
    is_deleted= _sql.Column(_sql.Boolean, default=False)