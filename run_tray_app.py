"""
딜러 데스크 로컬 서버 트레이 애플리케이션 실행 스크립트
"""
import os
import sys
import logging
from app_tray import main

if __name__ == "__main__":
    try:
        # 로깅 설정
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler("dealer_desk_tray.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        logger = logging.getLogger("dealer-desk-runner")
        
        logger.info("딜러 데스크 로컬 서버 트레이 애플리케이션을 시작합니다...")
        
        # 메인 함수 실행
        main()
        
    except KeyboardInterrupt:
        logger.info("키보드 인터럽트에 의해 애플리케이션이 종료되었습니다.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"애플리케이션 실행 중 오류 발생: {e}")
        sys.exit(1) 