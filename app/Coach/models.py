import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

class Coach(_database.Base):
    __tablename__ = "coach"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    coach_name = _sql.Column(_sql.String)
    is_deleted= _sql.Column(_sql.Boolean, default=False)


class CoachOrganization(_database.Base):
    __tablename__ = "coach_organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    coach_id = _sql.Column(_sql.Integer)
    org_id = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
