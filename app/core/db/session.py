import sqlalchemy as _sql
import sqlalchemy.ext.declarative as _declarative
import sqlalchemy.orm as _orm
from dotenv import load_dotenv
import os

# Load environment variables from .env file
load_dotenv()


# Retrieve environment variables
DATABASE_URL = os.environ.get("DATABASE_URL")

engine = _sql.create_engine(DATABASE_URL, pool_pre_ping=True, pool_recycle=300, echo=True)
SessionLocal = _orm.sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = _declarative.declarative_base()
