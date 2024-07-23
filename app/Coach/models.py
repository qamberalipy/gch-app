import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative


class Coach(_database.Base):
    __tablename__ = "coach"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    wallet_address = _sql.Column(_sql.String)
    own_coach_id = _sql.Column(_sql.String, nullable=True)
    profile_img = _sql.Column(_sql.String(150))  # varchar(150) in the image is likely a typo
    first_name = _sql.Column(_sql.String, nullable=False)
    last_name = _sql.Column(_sql.String, nullable=False)
    dob = _sql.Column(_sql.Date, nullable=False)
    gender = _sql.Column(_sql.String(10))  # varchar(10) in the image is likely the intended length
    email = _sql.Column(_sql.String, nullable=False, unique=True)
    password = _sql.Column(_sql.String(250))
    phone = _sql.Column(_sql.String(11))  # Assuming phone number should not include landline
    mobile_number = _sql.Column(_sql.String(11))
    notes = _sql.Column(_sql.String)
    source_id= _sql.Column(_sql.Integer)  # Removed foreign key reference
    country_id = _sql.Column(_sql.Integer)  # Removed foreign key reference
    city = _sql.Column(_sql.String(20))
    zipcode = _sql.Column(_sql.String(10))
    address_1 = _sql.Column(_sql.String(100))  # address 1 renamed to address_1 for clarity
    address_2 = _sql.Column(_sql.String(100))
    coach_since = _sql.Column(_sql.Date, nullable=False)
    bank_detail_id=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime)
    updated_at = _sql.Column(_sql.DateTime)
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean, default=False)

class CoachOrganization(_database.Base):
    __tablename__ = "coach_organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    coach_id = _sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    coach_status=_sql.Column(_sql.Boolean, default=True)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
