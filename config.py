import os
from pathlib import Path
from dotenv import load_dotenv
import sqlalchemy

BASE_DIR = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
INPUT_TABLE = "trendfragility.raw_data"

def _require(key:str) -> str:
    val = os.environ.get(key)
    if not val:
        raise EnvironmentError(f"{key} is not set")
    return val

PG_HOST = _require("PG_HOST")
PG_PORT = int(os.environ.get("PG_PORT",5432))
PG_DBNAME = _require("PG_DBNAME")
PG_USER = _require("PG_USER")
PG_PASSWORD = _require("PG_PASSWORD")
PG_SCHEMA = os.environ.get("PG_SCHEMA", "trendfragility")
api_url = "http://ec2-18-162-125-60.ap-east-1.compute.amazonaws.com:9000"

def get_engine() -> sqlalchemy.engine.base.Engine:
    connection_string = (
        f"postgresql+psycopg2://{PG_USER}:{PG_PASSWORD}"
        f"@{PG_HOST}:{PG_PORT}/{PG_DBNAME}"
    )
    return sqlalchemy.create_engine(connection_string)