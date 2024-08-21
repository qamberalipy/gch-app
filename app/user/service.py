from datetime import date,datetime
from typing import List, Dict, Any
from typing import Annotated, List
import jwt
from sqlalchemy import asc, desc, func, or_, text
import sqlalchemy.orm as _orm
from sqlalchemy.sql import and_  
import email_validator as _email_check
import fastapi as _fastapi
import fastapi.security as _security
import app.core.db.session as _database
import app.user.schema as _schemas
import app.user.models as _models
import random
import json
import pika
import time
import os
import bcrypt as _bcrypt
from . import models, schema
import logging
from app.Exercise.service import extract_columns
from collections import defaultdict
from app.user.models import StaffStatus
import smtplib
from email.mime.text import MIMEText
from fastapi import APIRouter, Depends, HTTPException, Header
from email.mime.multipart import MIMEMultipart

# Load environment variables

logger = logging.getLogger("uvicorn.error")
JWT_SECRET = os.getenv("JWT_SECRET")
JWT_EXPIRY = os.getenv("JWT_EXPIRY")
LOCAL_BASE_URL = os.getenv("LOCAL_BASE_URL")
BASE_URL = os.getenv("BASE_URL")
SENDER_PASSWORD = os.getenv("SENDER_PASSWORD")
SMTP_PORT = os.getenv("SMTP_PORT")
SMTP_SERVER = os.getenv("SMTP_SERVER")


oauth2schema = _security.OAuth2PasswordBearer(tokenUrl="api/login")
def create_database():
    # Create database tables
    return _database.Base.metadata.create_all(bind=_database.engine)

def get_db():
    # Dependency to get a database session
    db = _database.SessionLocal()
    try:
        yield db
    finally:
        db.close()

def verify_jwt(token: str):
    # Verify a JWT token
    credentials_exception = _fastapi.HTTPException(
        status_code=_fastapi.status.HTTP_401_UNAUTHORIZED,
        detail="Token Expired or Invalid",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        token = token.split("Bearer ")[1]
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        print("Time Difference", time.time() - payload["token_time"])
        if time.time() - payload["token_time"] > JWT_EXPIRY:
            print("Token Expired")
            raise credentials_exception

        return payload
    except:
        raise credentials_exception

def hash_password(password):
    # Hash a password
    return _bcrypt.hashpw(password.encode('utf-8'), _bcrypt.gensalt()).decode('utf-8')

async def get_user_by_email(email: str, db: _orm.Session):
    # Retrieve a user by email from the database
    print("Email: ", email)
    return db.query(_models.User).filter(
        and_(
            _models.User.email == email,
            _models.User.is_deleted == False
        )
    ).first()

async def create_organization(org: _schemas.OrganizationCreate,user_id,db: _orm.Session) -> models.Organization:
    org=org.dict()
    org['created_by']=user_id
    org['updated_by']=user_id
    org['created_at']=datetime.now()
    org['updated_at']=datetime.now()
    db_org = models.Organization(**org)
    db.add(db_org)
    db.commit()
    db.refresh(db_org)
    return db_org


async def get_organization(org_id: int, db: _orm.Session) -> models.Organization:
    return db.query(models.Organization).filter(models.Organization.id == org_id, models.Organization.is_deleted == False).first()

async def update_organization(org_id: int,user_id,org: _schemas.OrganizationUpdate, db: _orm.Session) -> models.Organization:
    db_org = db.query(models.Organization).filter(models.Organization.id == org_id, models.Organization.is_deleted == False).first()
    if not db_org:
        return None
    for key, value in org.dict(exclude_unset=True).items():
        setattr(db_org, key, value)
    db_org.updated_by=user_id
    db_org.updated_at=datetime.now()    
    db.commit()
    db.refresh(db_org)
    return db_org

async def delete_organization(org_id: int,user_id,db: _orm.Session):
    db_org = db.query(models.Organization).filter(models.Organization.id == org_id, models.Organization.is_deleted == False).first()
    if not db_org:
        return None
    db_org.is_deleted = True
    db_org.updated_by=user_id
    db_org.updated_at=datetime.now()
    db.commit()
    return db_org

async def get_opening_hours(org_id: int, db: _orm.Session) -> _models.Organization:
    return db.query(_models.Organization).filter(_models.Organization.id == org_id).first()

async def update_opening_hours(org_id: int,user_id:int,opening_hours_data: _schemas.OpeningHoursUpdate, db: _orm.Session):
    organization = db.query(_models.Organization).filter(_models.Organization.id == org_id).first()
    if organization:
        organization.opening_hours = opening_hours_data.opening_hours
        organization.opening_hours_notes = opening_hours_data.opening_hours_notes
        organization.updated_at = datetime.now()
        organization.updated_by=user_id
        db.commit()
        db.refresh(organization)
        return organization
    return None


async def create_user(user: _schemas.UserRegister, db: _orm.Session):
    try:
        valid = _email_check.validate_email(user.email)
        email = valid.email
    except _email_check.EmailNotValidError:
        raise _fastapi.HTTPException(status_code=400, detail="Please enter a valid email")

    hashed_password = hash_password(user.password)
    user_obj = _models.User(
        email=email, 
        first_name=user.first_name, 
        password=hashed_password,
        org_id=user.org_id
    )
    db.add(user_obj)
    db.commit()
    db.refresh(user_obj)
    return user_obj

async def create_organizationtest(organization: _schemas.OrganizationCreateTest, db: _orm.Session = _fastapi.Depends(get_db)):
    org = _models.Organization(name=organization.name)
    db.add(org)
    db.commit()
    db.refresh(org)
    return org

async def create_token(user: _models.User):
    # Create a JWT token for authentication
    user_obj = _schemas.User.from_orm(user)
    user_dict = user_obj.dict()
    print(user_dict)
    del user_dict["date_created"]
    user_dict['token_time'] = time.time()
    print("JWT_SECRET", JWT_SECRET)
    print("User Dict: ", user_dict)
    token = jwt.encode(user_dict, JWT_SECRET, algorithm="HS256")
    return dict(access_token=token, token_type="bearer")

async def get_current_user(token: str, db: _orm.Session = _fastapi.Depends(get_db)):
    # Get the current authenticated user from the JWT token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        user = db.query(_models.User).get(payload["id"])
    except:
        raise _fastapi.HTTPException(status_code=401, detail="Invalid Email or Password")
    return _schemas.UserSchema.from_orm(user)

def generate_otp():
    # Generate a random OTP
    return str(random.randint(100000, 999999))

async def get_user_by_email(email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(_models.User).filter(
        and_(
            _models.User.email == email,
            _models.User.is_deleted == False
        )
    ).first()

async def get_filtered_user_by_email(email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    user =  db.query(models.User).filter(models.User.email == email, _models.User.is_deleted == False).first()
    if user:
        return user
    else: 
        raise HTTPException(status_code=404, detail="User not found")

async def get_user_by_email_and_org(email: str, org_id: int,db: _orm.Session = _fastapi.Depends(get_db)):
    return db.query(models.User).filter(
        models.User.email == email,
        models.User.org_id == org_id
    ).first()

async def get_user_gym(user_email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    user = await get_filtered_user_by_email(user_email, db)
    if user:
        org_name, org_id, org_email = db.query(_models.Organization.name, _models.Organization.id , models.Organization.email).filter(and_(_models.Organization.id == user.org_id, _models.User.is_deleted == False)).first()
        return org_name, org_id, org_email, user

async def get_alluser_data(email: str, db: _orm.Session = _fastapi.Depends(get_db)):
    # Retrieve a user by email from the database
    result = (
        db.query(_models.User, _models.Organization.name)
        .join(_models.Organization, _models.User.org_id == _models.Organization.id)
        .filter(_models.User.email == email)
        .first()
    )
    
    if result:
        user, org_name = result
        return {
            "id": user.id,
            "first_name": user.first_name,
            "email": user.email,
            "date_created": user.created_at,
            "org_id": user.org_id,
            "org_name": org_name,
            "is_deleted": user.is_deleted
        }
    return None

async def update_user_password(user_id: int , org_id : int ,new_password : str, db: _orm.Session = _fastapi.Depends(get_db)):
    user = db.query(_models.User).filter(_models.User.id == user_id, _models.User.org_id == org_id, _models.User.is_deleted == False).first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
    user.password = new_password
    db.commit()
    return user
    
async def create_bank_account(bank_account:_schemas.BankAccountCreate,db: _orm.Session = _fastapi.Depends(get_db)):
    db_bank_account = models.BankAccount(**bank_account.dict())
    db.add(db_bank_account)
    db.commit()
    db.refresh(db_bank_account)
    return db_bank_account

async def create_staff(staff: _schemas.CreateStaff,user_id,db: _orm.Session = _fastapi.Depends(get_db)):
    staff_data = staff.dict()
    staff_data['created_by']=user_id
    staff_data['updated_by']=user_id
    staff_data['created_at']=datetime.now()
    staff_data['updated_at']=datetime.now()

    print(staff_data.pop("send_invitation"))
    db_staff = _models.User(**staff_data)
    db.add(db_staff)
    db.commit()
    db.refresh(db_staff)
    return {
            "status_code": "201",
            "id": db_staff.id,
            "message": "Staff created successfully"
        }
        
async def authenticate_user(email: str, password: str, db: _orm.Session):
    # Authenticate a user
    user = await get_user_by_email(email=email, db=db)

    if not user:
       raise HTTPException(status_code=400, detail="No account found associated with the provided email.")

    if not user.verify_password(password):
        return False
    return user

def generate_password_reset_html(name: str ,email :str ,gym_name: str, token: str) -> str:
    return f'''
    <html>
                    <head>
                        <title></title>
                        <meta http-equiv="Content-Type" content="text/html; charset=utf-8" />
                        <meta name="viewport" content="width=device-width, initial-scale=1">
                        <meta http-equiv="X-UA-Compatible" content="IE=edge" />
                        <style type="text/css">
                            /* FONTS */
                            @media screen {{
                                @font-face {{
                                    font-family: 'Lato';
                                    font-style: normal;
                                    font-weight: 400;
                                    src: local('Lato Regular'), local('Lato-Regular'),
                                    url(https://fonts.gstatic.com/s/lato/v11/qIIYRU-oROkIk8vfvxw6QvesZW2xOQ-xsNqO47m55DA.woff) format('woff');
                                }}
                                @font-face {{
                                    font-family: 'Lato';
                                    font-style: normal;
                                    font-weight: 700;
                                    src: local('Lato Bold'), local('Lato-Bold'),
                                    url(https://fonts.gstatic.com/s/lato/v11/qdgUG4U09HnJwhYI-uK18wLUuEpTyoUstqEm5AMlJo4.woff) format('woff');
                                }}
                                @font-face {{
                                    font-family: 'Lato';
                                    font-style: italic;
                                    font-weight: 400;
                                    src: local('Lato Italic'), local('Lato-Italic'),
                                    url(https://fonts.gstatic.com/s/lato/v11/RYyZNoeFgb0l7W3Vu1aSWOvvDin1pK8aKteLpeZ5c0A.woff) format('woff');
                                }}
                                @font-face {{
                                    font-family: 'Lato';
                                    font-style: italic;
                                    font-weight: 700;
                                    src: local('Lato Bold Italic'), local('Lato-BoldItalic'),
                                    url(https://fonts.gstatic.com/s/lato/v11/HkF_qI1x_noxlxhrhMQYELO3LdcAZYWl9Si6vvxL-qU.woff) format('woff');
                                }}
                            }}
                            /* CLIENT-SPECIFIC STYLES */
                            body, table, td, a {{
                                -webkit-text-size-adjust: 100%;
                                -ms-text-size-adjust: 100%;
                                color:#525167!important;
                            }}
                            table, td {{
                                mso-table-lspace: 0pt;
                                mso-table-rspace: 0pt;
                            }}
                            img {{
                                -ms-interpolation-mode: bicubic;
                            }}
                            /* RESET STYLES */
                            img {{
                                border: 0;
                                height: auto;
                                line-height: 100%;
                                outline: none;
                                text-decoration: none;
                            }}
                            table {{
                                border-collapse: collapse !important;
                            }}
                            body {{
                                height: 100% !important;
                                margin: 0 !important;
                                padding: 0 !important;
                                width: 100% !important;
                            }}
                            /* iOS BLUE LINKS */
                            a[x-apple-data-detectors] {{
                                color: inherit !important;
                                text-decoration: none !important;
                                font-size: inherit !important;
                                font-family: inherit !important;
                                font-weight: inherit !important;
                                line-height: inherit !important;
                            }}
                            /* ANDROID CENTER FIX */
                            div[style*="margin: 16px 0;"] {{
                                margin: 0 !important;
                            }}
                        </style>
                    </head>
                    <body style="background-color: #f4f4f4; margin: 0 !important; padding: 0 !important;">
                        <div style="display: none; font-size: 1px; color: #fefefe; line-height: 1px; font-family: 'Lato', Helvetica, Arial, sans-serif; max-height: 0px; max-width: 0px; opacity: 0; overflow: hidden;">Hi!</div>
                        <table border="0" cellpadding="0" cellspacing="0" width="100%">
                            <tbody>
                                <tr>
                                    <td bgcolor="#77DD77" align="center">
                                        <table border="0" cellpadding="0" cellspacing="0" width="550">
                                            <tbody>
                                                <tr>
                                                    <td align="center" valign="top" style="padding: 40px 10px 40px 10px;">
                                                        <a href="https://pifs.lts.com.fj" target="_blank"></a>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td bgcolor="#77DD77" align="center" style="padding: 0px 10px 0px 10px;">
                                        <table border="0" cellpadding="0" cellspacing="0" width="550">
                                            <tbody>
                                                <tr>
                                                    <td bgcolor="#ffffff" align="center" valign="top" style="padding: 40px 20px 20px 20px; border-radius: 4px 4px 0px 0px; color: #111111; font-family: 'Lato', Helvetica, Arial, sans-serif; font-size: 48px; font-weight: 500; letter-spacing: 2px; line-height: 48px;">
                                                        <h1 style="font-size: 28px; font-weight: 400; margin: 0;">Forgot Your Password?</h1>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td bgcolor="#f4f4f4" align="center" style="padding: 0px 10px 0px 10px;">
                                        <table border="0" cellpadding="0" cellspacing="0" width="550">
                                            <tbody>
                                                <tr>
                                                    <td bgcolor="#ffffff" align="left" style="padding: 20px 30px 20px 30px; color: #666666; font-family: 'Lato', Helvetica, Arial, sans-serif; font-size: 14px; font-weight: 400; line-height: 25px;">
                                                        <p style="margin: 0;">Hey {name},<br><br>We received a request to reset the password for your account. To proceed with resetting your password, please click the link below:<br><br>If you did not request this password reset, you can safely ignore this email. Your password will not be changed unless you follow the link and complete the reset process.<br><br>For security reasons, this link will expire in 30 minutes. If you do not reset your password within this time, you will need to request a new password reset.<br><br>If you encounter any issues or need further assistance, please contact our support team at {email}.<br><br>Thank you,<br><br>{gym_name}</p>
                                                    </td>
                                                    
                                                </tr>
                                                <tr>
                                                    <td bgcolor="#ffffff" align="left">
                                                        <table width="100%" border="0" cellspacing="0" cellpadding="0">
                                                            <tbody>
                                                                <tr>
                                                                    <td bgcolor="#ffffff" align="center" style="padding: 0px 30px 30px 30px;">
                                                                        <table border="0" cellspacing="0" cellpadding="0">
                                                                            <tbody>
                                                                                <tr>
                                                                                    <td align="center" style="border-radius: 3px;" bgcolor="#77DD77">
                                                                                        <a href="{LOCAL_BASE_URL if os.getenv("ENV") == "local" else BASE_URL}/reset_password/{token}" target="_blank" style="font-size: 20px; font-family: Helvetica, Arial, sans-serif; color: #ffffff; text-decoration: none; color: #ffffff; text-decoration: none; padding: 15px 25px; border-radius: 2px; border: 1px solid #77DD77; display: inline-block;">Reset Password</a>
                                                                                    </td>
                                                                                </tr>
                                                                            </tbody>
                                                                        </table>
                                                                    </td>
                                                                </tr>
                                                            </tbody>
                                                        </table>
                                                    </td>
                                                </tr>
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                                <tr>
                                    <td bgcolor="#f4f4f4" align="center" style="padding: 16px 10px 0px 10px;">
                                        <table border="0" cellpadding="0" cellspacing="0" width="550">
                                            <tbody>
                                                <tr>
                                                    <td bgcolor="#f4f4f4" align="left" style="padding: 0px 30px 16px 30px;color: #666666;font-family: 'Lato', Helvetica, Arial, sans-serif;font-size: 14px;font-weight: 400;line-height: 18px;">
                                                        <p style="margin: 0;">You received this email because your account password is being resetted</p>
                                                    </td>
                                                </tr>
                                               
                                            </tbody>
                                        </table>
                                    </td>
                                </tr>
                            </tbody>
                        </table>
                    </body>
                    </html>
    '''

def send_password_reset_email(recipient_email: str, subject: str, html_body: str) -> bool:
    sender_email = "letsmove.project2024@gmail.com"
    sender_password = SENDER_PASSWORD
    smtp_server = SMTP_SERVER
    smtp_port = SMTP_PORT

    # Create a MIME multipart message
    msg = MIMEMultipart("alternative")
    msg['Subject'] = subject
    msg['From'] = sender_email
    msg['To'] = recipient_email

    # Attach the HTML body
    part = MIMEText(html_body, "html")
    msg.attach(part)

    try:
        # Set up the SMTP server
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(sender_email, sender_password)

        # Send the email
        server.sendmail(sender_email, recipient_email, msg.as_string())
        server.quit()
        return True
    except Exception as e:
        print(f"Failed to send email: {str(e)}")
        return False

def get_all_countries( db: _orm.Session):
    return db.query(_models.Country).filter(_models.Country.is_deleted == False).all()

def get_all_sources( db: _orm.Session):
    return db.query(_models.Source).all()

async def get_one_staff(staff_id: int, db: _orm.Session):
    staff_detail = db.query(
        *models.User.__table__.columns,
        _models.Role.name.label("role_name")
        ).join(
            _models.Role, _models.User.role_id == _models.Role.id
        ).filter(
            _models.User.is_deleted == False,
            _models.User.id == staff_id
    ).first()
    print(staff_detail)
    if staff_detail:
        return staff_detail
    else :
        return None
    

async def update_staff(staff_id: int,user_id,staff_update: _schemas.UpdateStaff, db: _orm.Session):
    
    staff = db.query(_models.User).filter(and_(_models.User.id == staff_id,_models.User.is_deleted == False)).first()
    
    if staff is None:
        raise _fastapi.HTTPException(status_code=404, detail="Staff not found")
    
    update_data = staff_update.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(staff, key, value)
    
    staff.updated_at = datetime.now()
    staff.updated_by=user_id
    db.commit()
    db.refresh(staff)
    return staff


async def delete_staff(staff_id: int,user_id,db: _orm.Session):
    staff = db.query(_models.User).filter(and_(_models.User.id == staff_id,_models.User.is_deleted == False)).first()
    if staff is None:
        raise _fastapi.HTTPException(status_code=404, detail="Staff not found")
    
    staff.is_deleted = True
    staff.updated_by=user_id
    staff.updated_at=datetime.now()
    db.commit()
    return {"status":"201","detail":"Staff deleted successfully"}

def get_filtered_staff(org_id: int, params: _schemas.StaffFilterParams,db:_orm.Session=_fastapi.Depends(get_db)):
    
    sort_mapping = {
        "own_staff_id": text("staff.own_staff_id"),
        "first_name":text("staff.first_name"),
        "status": text("staff.status"),
        "last_checkin": text("staff.last_checkin"),
        "role_id": text("staff.role_id"),
        "activated_on": text("staff.activated_on"),
        "created_at":text("staff.created_at")
        }
    
    query = db.query(
        *models.User.__table__.columns, models.Role.name.label("role_name")
    ).join(
        models.Role, models.User.role_id == models.Role.id
    ).filter(
        models.User.org_id == org_id,
        models.User.is_deleted == False
    )

    total_counts = db.query(func.count()).select_from(query.subquery()).scalar()

    if params.staff_name:
        query = query.filter(or_(
            models.User.first_name.ilike(f"%{params.staff_name}%"),
            models.User.last_name.ilike(f"%{params.staff_name}%")
        ))

    if params.role_id:
        query = query.filter(models.Role.id.in_(params.role_id))
        
    if params.status:
        query = query.filter(models.User.status == params.status)    

    if params.search_key:
        search_pattern = f"%{params.search_key}%"
        query = query.filter(or_(
            models.User.own_staff_id.ilike(search_pattern),
            models.User.first_name.ilike(search_pattern),
            models.User.last_name.ilike(search_pattern),
            models.User.email.ilike(search_pattern),
            models.User.mobile_number.ilike(search_pattern),
            models.User.profile_img.ilike(search_pattern),
            models.User.notes.ilike(search_pattern),
            models.User.city.ilike(search_pattern),
            models.User.zipcode.ilike(search_pattern),
            models.User.address_1.ilike(search_pattern),
            models.User.address_2.ilike(search_pattern)
        ))

    if params.sort_key in sort_mapping.keys():       
        sort_order = desc(sort_mapping.get(params.sort_key)) if params.sort_order == "desc" else asc(sort_mapping.get(params.sort_key))
        query = query.order_by(sort_order)
    elif params.sort_key is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Sorting column not found.")

    filtered_counts = db.query(func.count()).select_from(query.subquery()).scalar()
    
    query=query.offset(params.offset).limit(params.limit)
    
    staff = query.all()
    staff_data = [_schemas.GetStaffResponse.from_orm(user) for user in staff]

    return {'data': staff_data, 'total_counts': total_counts, 'filtered_counts': filtered_counts}

    
async def check_role(role: _schemas.RoleCreate, db: _orm.Session = _fastapi.Depends(get_db)):
    ch_role = db.query(_models.Role).filter(_models.Role.name == role.name, _models.Role.org_id == role.org_id).first()
    
    if ch_role is not None:
        raise _fastapi.HTTPException(status_code=400, detail="Role already exists")

    if len(role.resource_id) != len(role.access_type):
        raise _fastapi.HTTPException(status_code=400, detail="Resource ID and Access Type should be equal")

    return True

async def create_role(role: _schemas.RoleCreate,user_id,db: _orm.Session = _fastapi.Depends(get_db)):
    db_role = _models.Role(
        name=role.name,
        org_id=role.org_id,
        status = role.status,
        created_by=user_id,
        updated_by=user_id,
        created_at=datetime.now(),
        updated_at=datetime.now(),
        is_deleted=0
    )
    db.add(db_role)
    db.commit()
    db.refresh(db_role)

    for i in range(len(role.resource_id)):
        db_permission = _models.Permission(
            role_id=db_role.id,
            resource_id=role.resource_id[i],
            access_type=role.access_type[i],
            created_by=user_id,
            updated_by=user_id,
            created_at=datetime.now(),
            updated_at=datetime.now(),
            is_deleted=0
        )
        db.add(db_permission)
    db.commit()
    db.refresh(db_permission)
    return db_role


async def get_all_roles(org_id: int, db: _orm.Session):
    data = db.query(_models.Role.name, _models.Role.id, _models.Role.status)\
        .filter(_models.Role.is_deleted == False, _models.Role.org_id == org_id).all()
    data = [{"id": role.id, "name": role.name, "status": role.status} for role in data]

    return data

async def temp_get_role(role_id: int, db: _orm.Session):
    role = db.query(_models.Role).filter(_models.Role.id == role_id, _models.Role.is_deleted == False).first()
    if role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
    
    permissions = db.query(_models.Resource.name.label("resource_name"), _models.Permission.access_type, _models.Role.org_id, 
        _models.Role.status, _models.Permission.id.label("permission_id"), _models.Role.id.label("role_id"), _models.Resource.code, 
        _models.Resource.link, _models.Resource.icon, _models.Resource.is_parent, _models.Resource.parent)\
        .join(_models.Permission, _models.Resource.id == _models.Permission.resource_id)\
        .join(_models.Role, _models.Permission.role_id == _models.Role.id)\
        .filter(_models.Permission.role_id == role_id, _models.Permission.is_deleted == False).all()

    return permissions


from collections import defaultdict

async def test_get_role(role_id: int, db: _orm.Session):
    role = db.query(_models.Role).filter(
        _models.Role.id == role_id,
        _models.Role.is_deleted == False
    ).first()

    if role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")

    resources = db.query(
        _models.Resource
    ).options(
        _orm.joinedload(_models.Resource.children)
    ).all()

    permissions = db.query(
        _models.Permission
    ).filter(
        _models.Permission.role_id == role_id,
        _models.Permission.is_deleted == False
    ).all()
    
    permission_dict = {permission.resource_id: permission.access_type for permission in permissions}

    def process_resource(resource) -> Dict[str, Any]:
        return {
            "id": resource.id,
            "name": resource.name,
            "code": resource.code,
            "parent": resource.parent,
            "is_parent": resource.is_parent,
            "is_root": resource.is_root,
            "link": resource.link,
            "icon": resource.icon,
            "access_type": permission_dict.get(resource.id),
            "children": [process_resource(child) for child in resource.children] #  if not child.is_parent
        }

    # Filter root resources and build the response
    root_resources = [resource for resource in resources if resource.is_root]
    result = [process_resource(resource) for resource in root_resources]

    return result


async def get_role(role_id: int, db: _orm.Session):
    role = db.query(_models.Role).filter(_models.Role.id == role_id, _models.Role.is_deleted == False).first()
    if role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
    
    permissions = db.query(
        _models.Resource.name.label("resource_name"),
        _models.Permission.access_type,
        _models.Role.org_id,
        _models.Role.status,
        _models.Permission.id.label("permission_id"),
        _models.Role.id.label("role_id"),
        _models.Role.name.label("role_name"),
        _models.Resource.code,
        _models.Resource.link,
        _models.Resource.icon,
        _models.Resource.is_parent,
        _models.Resource.parent
    ).join(
        _models.Permission, _models.Resource.id == _models.Permission.resource_id
    ).join(
        _models.Role, _models.Permission.role_id == _models.Role.id
    ).filter(
        _models.Permission.role_id == role_id,
        _models.Permission.is_deleted == False
    ).all()

    # Create a dictionary to store roles by their code
    resource_dict = {p.code: _schemas.RoleRead(**p._asdict(), subRows=[]) for p in permissions if p.code is not None}

    # Include parent roles in resource_dict if they are missing
    for perm in permissions:
        if perm.parent and perm.parent not in resource_dict:
            parent_role = db.query(
                _models.Resource.name.label("resource_name"),
                _models.Role.org_id,
                _models.Role.status,
                _models.Role.id.label("role_id"),
                _models.Resource.code,
                _models.Resource.link,
                _models.Resource.icon,
                _models.Resource.is_parent,
                _models.Resource.parent
            ).filter(
                _models.Resource.code == perm.parent,
                _models.Role.id == role_id
            ).first()
            if parent_role:
                resource_dict[perm.parent] = _schemas.RoleRead(
                    resource_name=parent_role.resource_name,
                    role_id=parent_role.role_id,
                    org_id=parent_role.org_id,
                    status=parent_role.status,
                    permission_id=None,
                    access_type=None,
                    is_parent=parent_role.is_parent,
                    parent=parent_role.parent,
                    code=parent_role.code,
                    link=parent_role.link,
                    icon=parent_role.icon,
                    is_deleted=False,
                    subRows=[]
                )

    # Create a dictionary to store parent-child relationships
    children_map = defaultdict(list)
    for perm in permissions:
        if perm.parent and perm.parent in resource_dict:
            children_map[perm.parent].append(_schemas.RoleRead(**perm._asdict(), subRows=[]))

    # Assign children to their respective parents
    for code, role in resource_dict.items():
        if code in children_map:
            role.subRows.extend(children_map[code])

    # Collect all roles (root roles and their children)
    all_roles = []
    for code, role in resource_dict.items():
        if role.parent is None:
            all_roles.append(role)

    return all_roles


async def edit_role(role: _schemas.RoleUpdate,user_id,db: _orm.Session):
    db_role = db.query(_models.Role).filter(_models.Role.id == role.id, _models.Role.is_deleted == False).first()
    
    if db_role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
    
    update_data = role.dict(exclude_unset=True)
    for key, value in update_data.items():
        setattr(db_role, key, value)
    
    db.commit()
    db.refresh(db_role)

    if role.resource_id is None or role.access_type is None:
        return db_role

    if len(role.resource_id) != len(role.access_type):
        raise _fastapi.HTTPException(status_code=400, detail="Resource ID and Access Type should be equal")
    

    permissions = db.query(_models.Permission).filter(_models.Permission.role_id == role.id and _models.Permission.resource_id not in role.resource_id).all()
    print("Check Permissions: ", permissions)
    for permission in permissions:
        permission.is_deleted = 1
        permission.updated_at=datetime.now()
    db.commit()

    for i in range(len(role.resource_id)):
        db_permission = db.query(_models.Permission).filter(_models.Permission.role_id == role.id, _models.Permission.resource_id == role.resource_id[i]).first()
        if db_permission is None:
            db_permission = _models.Permission(
                role_id=role.id,
                resource_id=role.resource_id[i],
                access_type=role.access_type[i],
                created_by=user_id,
                updated_by=user_id,
                is_deleted=0
            )
            db.add(db_permission)
        else:
            print("Here: ")
            db_permission.is_deleted = 0
            db_permission.access_type = role.access_type[i]
            db_permission.updated_at = datetime.now()
        db.commit()
    db.refresh(db_permission)
    return db_role

async def delete_role(role_id: int, db: _orm.Session):
    print("Role ID: ", role_id)
    role = db.query(_models.Role).filter(_models.Role.id == role_id, _models.Role.is_deleted == False).first()
    print("Role: ", role)
    if role is None:
        raise _fastapi.HTTPException(status_code=404, detail="Role not found")
    
    role.is_deleted = 1
    role.status = 'inactive'
    db.commit()

    permissions = db.query(_models.Permission).filter(_models.Permission.role_id == role_id).all()
    for permission in permissions:
        permission.is_deleted = 1
        permission.updated_at=datetime.now()
    db.commit()
    return {"detail": "Role deleted successfully"}

async def get_all_resources(db: _orm.Session):
    data = db.query(_models.Resource).filter(_models.Resource.is_deleted == False).options(
        _orm.joinedload(_models.Resource.children)
    ).order_by(_models.Resource.id).all()
    data = [d for d in data if d.is_root]
    return data

async def get_Total_count_staff(org_id: int, db: _orm.Session = _fastapi.Depends(get_db)) -> int:
    total_staffs = db.query(func.count(models.User.id)).filter(
        _models.User.org_id == org_id
    ).scalar()
    print(total_staffs)
    return total_staffs

def get_filters(

    search_key: Annotated[str, _fastapi.Query(title="Search Key")] = None,
    staff_name: Annotated[str , _fastapi.Query(title="Staff Name")] = None,
    role_id: Annotated[list[int],_fastapi.Query(title="Role Name")]=None,
    sort_key: Annotated[str,_fastapi.Query(title="Sort Key")]=None,
    status: Annotated[StaffStatus,_fastapi.Query(title="Status")]=None,
    sort_order: Annotated[str,_fastapi.Query(title="Sort Order")]="desc",
    limit: Annotated[int, _fastapi.Query(description="Pagination Limit")] = None,
    offset: Annotated[int, _fastapi.Query(description="Pagination offset")] = None):
    
    return _schemas.StaffFilterParams(
        search_key=search_key,
        sort_key=sort_key,
        sort_order=sort_order,
        status=status,
        staff_name=staff_name,
        role_id=role_id,
        limit=limit,
        offset = offset
    )