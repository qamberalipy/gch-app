import datetime as _dt
from datetime import date
import sqlalchemy as _sql
import sqlalchemy.orm as _orm
import app.core.db.session as _database
import bcrypt as _bcrypt
import sqlalchemy.ext.declarative as _declarative
from enum import Enum as PyEnum

class StaffStatus(str,PyEnum):
    active='active'
    inactive='inactive'
    pending='pending'    
    
class RoleStatus(str,PyEnum):
    active='active'
    inactive='inactive'
         
class User(_database.Base):
    __tablename__ = "staff"

    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    own_staff_id=_sql.Column(_sql.String)
    profile_img = _sql.Column(_sql.String(150))
    password = _sql.Column(_sql.String(100))
    first_name = _sql.Column(_sql.String(50))
    last_name = _sql.Column(_sql.String(50))
    gender = _sql.Column(_sql.String(10))
    dob = _sql.Column(_sql.DateTime)
    email = _sql.Column(_sql.String(100), index=True)
    phone = _sql.Column(_sql.String(11))
    activated_on = _sql.Column(_sql.Date)
    reset_token=_sql.Column(_sql.String)
    last_checkin = _sql.Column(_sql.DateTime)
    last_online = _sql.Column(_sql.DateTime)
    status = _sql.Column(_sql.Enum(StaffStatus))
    phone = _sql.Column(_sql.String(15))  # Assuming phone number should not include landline
    mobile_number = _sql.Column(_sql.String(15))
    notes = _sql.Column(_sql.String)
    source_id = _sql.Column(_sql.Integer)
    org_id =_sql.Column(_sql.Integer)
    role_id = _sql.Column(_sql.Integer)
    country_id = _sql.Column(_sql.Integer)
    city = _sql.Column(_sql.String(20))
    zipcode = _sql.Column(_sql.String)
    address_1 = _sql.Column(_sql.String(100))
    address_2 = _sql.Column(_sql.String)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean, default=False)
    
    def verify_password(self, password: bytes):
        if self.password is not None:
            print("In Verify Password", password, self.password.encode('utf-8'))
            return _bcrypt.checkpw(password.encode('utf-8'), self.password.encode('utf-8'))
        else:
            False

class Country(_database.Base):
    __tablename__ = "country"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    country = _sql.Column(_sql.String)
    country_code = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)
    
class Source(_database.Base):
    __tablename__ = "source"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True)
    source = _sql.Column(_sql.String)
           
class Organization(_database.Base):
    __tablename__ = "organization"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String)
    email = _sql.Column(_sql.String)
    profile_img = _sql.Column(_sql.String(150))  
    business_type = _sql.Column(_sql.String(150))
    description = _sql.Column(_sql.String)
    address = _sql.Column(_sql.String(100)) 
    zipcode = _sql.Column(_sql.String(10))
    country_id = _sql.Column(_sql.Integer)
    city = _sql.Column(_sql.String(20))
    facebook_page_url=_sql.Column(_sql.String)
    website_url=_sql.Column(_sql.String)
    timezone = _sql.Column(_sql.String(20))
    language =_sql.Column(_sql.String(20))
    company_reg_no =_sql.Column(_sql.String(20))
    vat_reg_no =_sql.Column(_sql.String(20))
    club_key=_sql.Column(_sql.String)
    api_key=_sql.Column(_sql.String)
    hide_for_nonmember= _sql.Column(_sql.Boolean, default=False)
    opening_hours=_sql.Column(_sql.JSON)
    opening_hours_notes=_sql.Column(_sql.String)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted= _sql.Column(_sql.Boolean, default=False)

class UserRole(_database.Base):
    __tablename__ = "user_role_mapping"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    user_id=_sql.Column(_sql.Integer)
    role_id=_sql.Column(_sql.Integer)
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted=_sql.Column(_sql.Boolean)

# class Role(_database.Base):
#     __tablename__ = "role"
#     id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
#     name = _sql.Column(_sql.String(50))
#     org_id = _sql.Column(_sql.Integer)
#     status = _sql.Column(_sql.Boolean)
#     is_deleted=_sql.Column(_sql.Boolean)


# class Resource(_database.Base):
#     __tablename__ = "resource"
#     id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
#     name=_sql.Column(_sql.String(50))
#     code=_sql.Column(_sql.String(50))
#     parent = _sql.Column(_sql.String(50))
#     is_parent = _sql.Column(_sql.Boolean)
#     is_root = _sql.Column(_sql.Boolean)
#     link = _sql.Column(_sql.String(50))
#     icon = _sql.Column(_sql.String(50))
#     created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now)
#     updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now)
#     created_by = _sql.Column(_sql.Integer)
#     updated_by = _sql.Column(_sql.Integer)
#     is_deleted=_sql.Column(_sql.Boolean)

#     # self join of parent with code
#     rel_parent = _orm.relationship(
#         "Resource",
#         lazy="select",
#         primaryjoin="foreign(Resource.parent)==Resource.code",
#         remote_side=[code],
#         back_populates="children"
#     )
#     children = _orm.relationship(
#         "Resource",
#         lazy="select",
#         primaryjoin="Resource.code==foreign(Resource.parent)",
#         remote_side=[parent],
#         back_populates="rel_parent"
#     )
    

# class Permission(_database.Base):
#     __tablename__ = 'permission'
#     id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
#     role_id= _sql.Column(_sql.Integer)
#     resource_id= _sql.Column(_sql.Integer)
#     access_type = _sql.Column(_sql.String(50))
#     created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now)
#     updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now)
#     created_by = _sql.Column(_sql.Integer)
#     updated_by = _sql.Column(_sql.Integer)
#     is_deleted=_sql.Column(_sql.Boolean)

class Role(_database.Base):
    __tablename__ = "role"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String(50))
    org_id = _sql.Column(_sql.Integer)
    status = _sql.Column(_sql.Enum(RoleStatus))
    is_deleted = _sql.Column(_sql.Boolean)
    
    # permissions = _orm.relationship(
    #     "Permission",
    #     back_populates="role",
    #     primaryjoin="Permission.role_id==foreign(Role.id)",
    #     lazy="select"
    # )


class Resource(_database.Base):
    __tablename__ = "resource"
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    name = _sql.Column(_sql.String(50))
    code = _sql.Column(_sql.String(50))
    parent = _sql.Column(_sql.String(50))
    is_parent = _sql.Column(_sql.Boolean)
    is_root = _sql.Column(_sql.Boolean)
    link = _sql.Column(_sql.String(50))
    icon = _sql.Column(_sql.String(50))
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean)

    # self join of parent with code
    rel_parent = _orm.relationship(
        "Resource",
        lazy="select",
        primaryjoin="foreign(Resource.parent)==Resource.code",
        remote_side=[code],
        back_populates="children"
    )
    children = _orm.relationship(
        "Resource",
        lazy="select",
        primaryjoin="Resource.code==foreign(Resource.parent)",
        remote_side=[parent],
        back_populates="rel_parent"
    )

    # permissions = _orm.relationship(
    #     "Permission",
    #     back_populates="resource",
    #     primaryjoin="Resource.id==foreign(Permission.resource_id)",
    #     lazy="select"
    # )


class Permission(_database.Base):
    __tablename__ = 'permission'
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    role_id = _sql.Column(_sql.Integer)
    resource_id = _sql.Column(_sql.Integer)
    access_type = _sql.Column(_sql.String(50))
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted = _sql.Column(_sql.Boolean)

    # role = _orm.relationship(
    #     "Role",
    #     primaryjoin="Permission.role_id==foreign(Role.id)",
    #     back_populates="permissions",
    #     lazy="select"
    # )
    # resource = _orm.relationship(
    #     "Resource",
    #     primaryjoin="Resource.id==foreign(Permission.resource_id)",
    #     back_populates="permissions"
    # )

    
class Bank_detail(_database.Base):
    __tablename__ = 'bank_detail'
    id = _sql.Column(_sql.Integer, primary_key=True, index=True, autoincrement=True)
    org_id= _sql.Column(_sql.Integer)
    user_type= _sql.Column(_sql.String)
    bank_name = _sql.Column(_sql.String(50))
    iban_no = _sql.Column(_sql.String(50))
    acc_holder_name = _sql.Column(_sql.String(50))
    swift_code = _sql.Column(_sql.String(50))
    created_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    updated_at = _sql.Column(_sql.DateTime, default=_dt.datetime.now())
    created_by = _sql.Column(_sql.Integer)
    updated_by = _sql.Column(_sql.Integer)
    is_deleted=_sql.Column(_sql.Boolean)    
    
class Transaction(_database.Base):
    __tablename__ = 'transaction'

    id = _sql.Column(_sql.Integer, primary_key=True, server_default=_sql.text("nextval('transaction_id_seq'::regclass)"), autoincrement=True)
    transaction_hash = _sql.Column(_sql.String, unique=True)
    _from = _sql.Column('from', _sql.String)
    to = _sql.Column(_sql.String)
    value = _sql.Column(_sql.String)
    event_type = _sql.Column(_sql.String)
    status = _sql.Column(_sql.Enum('pending', 'success', 'failed', name='TransactionEnums'), nullable=False, server_default=_sql.text("'pending'::\"TransactionEnums\""))
    created_at = _sql.Column(_sql.TIMESTAMP, nullable=False, server_default=_sql.text("CURRENT_TIMESTAMP"))
    updated_at = _sql.Column(_sql.TIMESTAMP, nullable=False, server_default=_sql.text("CURRENT_TIMESTAMP"))
