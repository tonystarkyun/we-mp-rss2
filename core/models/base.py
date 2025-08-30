from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime,Date,ForeignKey,Boolean,Enum,Table
from sqlalchemy import inspect
from sqlalchemy.exc import SQLAlchemyError
from core.config import cfg

if cfg.get("db","sqlite").startswith("sqlite"):
    from sqlalchemy import Text
else:
    from sqlalchemy.dialects.mysql import MEDIUMTEXT as Text

class DataStatus():
    DELETED:int = 1000
    ACTIVE:int = 1
    INACTIVE:int = 2
    PENDING:int = 3
    COMPLETED:int = 4
    FAILED:int = 5
DATA_STATUS=DataStatus()
Base = declarative_base()