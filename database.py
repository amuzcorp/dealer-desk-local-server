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

def create_test_user_data():
    import models
    from datetime import datetime
    import random
    
    db = SessionLocal()
    try:
        # 이미 테스트 사용자가 있는지 확인
        existing_user = db.query(models.UserData).filter(
            models.UserData.name.like("guest%")
        ).first()
        
        if existing_user:
            print("테스트 사용자가 이미 존재합니다.")
            return

        for i in range(10):
            # 테스트 일반 사용자 생성
            normal_user = models.UserData(
                name=f"테스트사용자{i}",
                phone_number=f"01012345678{i}",
                regist_mail=f"test{i}@test.com",
                register_at=datetime.now(),
                last_visit_at=datetime.now(),
                point=5000,
                total_point=5000,
                game_join_count=5,
                visit_count=10
            )
        
            db.add(normal_user)
        db.commit()
        
        print("테스트 사용자가 성공적으로 생성되었습니다.")
    except Exception as e:
        print(f"테스트 사용자 생성 중 오류 발생: {e}")
    finally:
        db.close()

# 테스트 데이터 생성 함수
def create_test_purchase_data():
    import models
    from datetime import datetime
    
    db = SessionLocal()
    try:
        # 이미 테스트 데이터가 있는지 확인
        existing_data = db.query(models.PurchaseData).filter(
            models.PurchaseData.user_id == 1001, 
            models.PurchaseData.purchase_type.in_(["BUYIN", "REBUYIN"])
        ).first()
        
        if existing_data:
            print("테스트 구매 데이터가 이미 존재합니다.")
            return
            
        # 테스트 사용자 ID
        test_user_id = 1001
        
        # 1. SUCCESS 상태의 BUYIN 데이터
        success_buyin = models.PurchaseData(
            purchase_type="LOCAL_PAY",
            game_id=1,
            user_id=test_user_id,
            purchased_at=datetime.now(),
            item="BUYIN",
            payment_status="COMPLETED",
            status="SUCCESS",
            price=10000,
            used_points=0
        )
        
        # 2. WAITING 상태의 BUYIN 데이터
        waiting_buyin = models.PurchaseData(
            purchase_type="LOCAL_PAY",
            game_id=1,
            user_id=test_user_id,
            purchased_at=datetime.now(),
            item="BUYIN",
            payment_status="WAITING",
            status="WAITING",
            price=10000,
            used_points=0
        )
        
        # 3 & 4. WAITING 상태의 REBUYIN 데이터 (2개)
        waiting_rebuyin1 = models.PurchaseData(
            purchase_type="LOCAL_PAY",
            game_id=1,
            user_id=test_user_id,
            purchased_at=datetime.now(),
            item="REBUYIN",
            payment_status="WAITING",
            status="WAITING",
            price=5000,
            used_points=0
        )
        
        waiting_rebuyin2 = models.PurchaseData(
            purchase_type="LOCAL_PAY",
            game_id=1,
            user_id=test_user_id,
            purchased_at=datetime.now(),
            item="REBUYIN",
            payment_status="WAITING",
            status="WAITING",
            price=5000,
            used_points=0
        )
        
        # 5. PAYMENT_CHIP 상태의 BUYIN 데이터
        payment_chip_buyin = models.PurchaseData(
            purchase_type="LOCAL_PAY",
            game_id=1,
            user_id=test_user_id,
            purchased_at=datetime.now(),
            item="BUYIN",
            payment_status="COMPLETED",
            status="PAYMENT_CHIP",
            price=10000,
            used_points=0
        )
        
        # 데이터베이스에 추가
        db.add(success_buyin)
        db.add(waiting_buyin)
        db.add(waiting_rebuyin1)
        db.add(waiting_rebuyin2)
        db.add(payment_chip_buyin)
        
        db.commit()
        print("테스트 구매 데이터가 성공적으로 생성되었습니다.")
    except Exception as e:
        db.rollback()
        print(f"테스트 데이터 생성 중 오류 발생: {e}")
    finally:
        db.close() 