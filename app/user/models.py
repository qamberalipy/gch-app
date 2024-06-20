import datetime as _dt
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative

# Base = _declarative.declarative_base()

class User(_database.Base):
    __tablename__ = "users"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    username = _sql.Column(_sql.String)
    password = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String, unique=True, index=True)
    # otp = _sql.Column(_sql.Integer)
    date_created = _sql.Column(_sql.DateTime, default=_dt.datetime.utcnow)
    # is_verified = _sql.Column(_sql.Boolean , default=False)
    # role_id = _sql.Column(_sql.Integer ,index=True)
    # organization_id = _sql.Column(_sql.Integer, index=True)
    
    def verify_password(self, password: bytes):
        print("In Verify Password", password, self.password.encode('utf-8'))
        return _bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))


_database.Base.metadata.create_all(_database.engine)