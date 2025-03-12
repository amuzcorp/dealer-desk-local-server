import os
import sys
import subprocess
import shutil
import logging

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("dealerdesk_launcher.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("DealerDeskLauncher")

def ensure_internal_directory():
    """_internal 디렉토리가 존재하는지 확인하고, 필요하면 생성합니다."""
    logger.info("DealerDesk 런처 시작")
    
    # 현재 스크립트 위치 확인
    current_dir = os.path.dirname(os.path.abspath(__file__))
    exe_path = os.path.join(current_dir, "dist", "DealerDesk", "DealerDesk.exe")
    internal_dir = os.path.join(current_dir, "dist", "DealerDesk", "_internal")
    
    logger.info(f"현재 디렉토리: {current_dir}")
    logger.info(f"실행 파일 경로: {exe_path}")
    logger.info(f"_internal 디렉토리 경로: {internal_dir}")
    
    # _internal 디렉토리 확인
    if not os.path.exists(internal_dir):
        logger.warning("_internal 디렉토리가 없습니다. 생성합니다.")
        os.makedirs(internal_dir, exist_ok=True)
    
    # 필요한 파일이 _internal에 있는지 확인
    required_files = [
        "main.py", 
        "web_server.py", 
        "database.py", 
        "schemas.py", 
        "models.py", 
        "auth_manager.py", 
        "central_socket.py",
        "app_icon.ico",
        "sql_app.db"
    ]
    
    required_dirs = ["app", "databases", "Controllers"]
    
    # 파일 복사 여부 확인
    files_to_copy = []
    for file in required_files:
        internal_file_path = os.path.join(internal_dir, file)
        source_file_path = os.path.join(current_dir, file)
        
        if not os.path.exists(internal_file_path) and os.path.exists(source_file_path):
            files_to_copy.append((source_file_path, internal_file_path))
    
    # 디렉토리 복사 여부 확인
    dirs_to_copy = []
    for dir_name in required_dirs:
        internal_dir_path = os.path.join(internal_dir, dir_name)
        source_dir_path = os.path.join(current_dir, dir_name)
        
        if not os.path.exists(internal_dir_path) and os.path.exists(source_dir_path):
            dirs_to_copy.append((source_dir_path, internal_dir_path))
    
    # 파일 복사
    for src, dest in files_to_copy:
        logger.info(f"파일 복사: {src} -> {dest}")
        try:
            shutil.copy2(src, dest)
        except Exception as e:
            logger.error(f"파일 복사 중 오류 발생: {str(e)}")
    
    # 디렉토리 복사
    for src, dest in dirs_to_copy:
        logger.info(f"디렉토리 복사: {src} -> {dest}")
        try:
            shutil.copytree(src, dest)
        except Exception as e:
            logger.error(f"디렉토리 복사 중 오류 발생: {str(e)}")
    
    return exe_path, internal_dir

def run_dealerdesk():
    """DealerDesk 애플리케이션을 실행합니다."""
    exe_path, internal_dir = ensure_internal_directory()
    
    if os.path.exists(exe_path):
        logger.info(f"DealerDesk.exe 실행: {exe_path}")
        try:
            # 환경 변수 설정 (DealerDesk.exe가 _internal 디렉토리를 찾을 수 있도록)
            env = os.environ.copy()
            env["INTERNAL_DIR"] = internal_dir
            
            # 애플리케이션 실행
            subprocess.Popen([exe_path], env=env)
            logger.info("DealerDesk.exe가 성공적으로 시작되었습니다.")
        except Exception as e:
            logger.error(f"DealerDesk.exe 실행 중 오류 발생: {str(e)}")
    else:
        logger.error(f"DealerDesk.exe를 찾을 수 없습니다: {exe_path}")
        print(f"오류: DealerDesk.exe를 찾을 수 없습니다. '{exe_path}'")
        
        # 대안으로 tray_app.py 직접 실행 시도
        tray_app_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "tray_app.py")
        if os.path.exists(tray_app_path):
            logger.info(f"tray_app.py 실행 시도: {tray_app_path}")
            try:
                subprocess.Popen([sys.executable, tray_app_path])
                logger.info("tray_app.py가 성공적으로 시작되었습니다.")
            except Exception as e:
                logger.error(f"tray_app.py 실행 중 오류 발생: {str(e)}")
        else:
            logger.error("실행 가능한 파일을 찾을 수 없습니다.")

if __name__ == "__main__":
    run_dealerdesk() 