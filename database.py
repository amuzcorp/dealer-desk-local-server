from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

# encoding 파라미터를 제거하고 기본 연결 문자열 사용
SQLALCHEMY_DATABASE_URL = "sqlite:///./sql_app.db"
# PostgreSQL을 사용하는 경우:
# SQLALCHEMY_DATABASE_URL = "postgresql://user:password@localhost/dbname"

# 데이터베이스 엔진 생성
engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False}  # SQLite를 위한 설정 복원
)

# SQLite 연결에 대한 이벤트 리스너 추가
@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA encoding='UTF-8'")
    cursor.close()

# 세션 로컬 클래스 생성
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base 클래스 생성
Base = declarative_base()

# DB 세션 의존성
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close() 