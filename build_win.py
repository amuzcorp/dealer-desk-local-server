import os
import shutil
import subprocess
import sys

def ensure_directory(directory):
    """지정된 디렉토리가 존재하는지 확인하고, 없으면 생성합니다."""
    if not os.path.exists(directory):
        os.makedirs(directory)
        print(f"디렉토리 생성됨: {directory}")

def copy_directory_contents(src, dest):
    """소스 디렉토리의 내용을 목적지 디렉토리로 복사합니다."""
    if not os.path.exists(src):
        print(f"경고: 소스 디렉토리가 존재하지 않습니다: {src}")
        return False
        
    ensure_directory(dest)
    
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dest, item)
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)
    
    return True

def install_requirements():
    """필요한 패키지를 설치합니다."""
    subprocess.run([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
    subprocess.run([sys.executable, "-m", "pip", "install", "pyinstaller"])

def build_application():
    """PyInstaller를 사용하여 응용 프로그램을 빌드합니다."""
    # 이전 빌드 정리
    if os.path.exists("build"):
        shutil.rmtree("build")
    if os.path.exists("dist"):
        shutil.rmtree("dist")
    
    # PyInstaller 명령 생성
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=DealerDeskServer",
        "--icon=icon.ico" if os.path.exists("icon.ico") else "",
        "--add-data=templates;templates" if os.path.exists("templates") else "",
        "--add-data=static;static" if os.path.exists("static") else "",
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.lifespan",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.lifespan.off",
        "--noconsole",
        "main.py"
    ]
    
    # 빈 문자열 항목 제거
    pyinstaller_cmd = [cmd for cmd in pyinstaller_cmd if cmd]
    
    # PyInstaller 실행
    subprocess.run(pyinstaller_cmd)
    
    # 필요한 추가 파일 복사
    additional_dirs = ["Controllers", "models", "schemas"]
    for dir_name in additional_dirs:
        if os.path.exists(dir_name):
            copy_directory_contents(dir_name, f"dist/DealerDeskServer/{dir_name}")
            
    # SQLite 데이터베이스가 있는 경우 복사 (data 디렉토리 가정)
    if os.path.exists("data"):
        copy_directory_contents("data", "dist/DealerDeskServer/data")
    
    # 환경 설정 파일 복사 (.env 파일이 있는 경우)
    if os.path.exists(".env"):
        shutil.copy2(".env", "dist/DealerDeskServer/.env")
    
    # web_server.py 파일이 있는 경우 복사
    if os.path.exists("web_server.py"):
        shutil.copy2("web_server.py", "dist/DealerDeskServer/web_server.py")
    
    print("빌드 완료! dist/DealerDeskServer 디렉토리에 애플리케이션이 생성되었습니다.")

def create_launcher():
    """시작 배치 파일을 생성합니다."""
    with open("dist/DealerDeskServer/start_server.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo 딜러 데스크 서버를 시작합니다...\n")
        f.write("start DealerDeskServer.exe\n")
        f.write("echo 브라우저를 열고 http://localhost:3000 으로 접속하세요\n")
        f.write("timeout /t 5\n")
        f.write("start http://localhost:3000\n")
        f.write("exit\n")

if __name__ == "__main__":
    print("딜러 데스크 API 서버 빌드 스크립트 시작...")
    
    install_requirements()
    build_application()
    create_launcher()
    
    print("모든 빌드 프로세스가 완료되었습니다!")
    print("dist/DealerDeskServer 폴더에서 start_server.bat 파일을 실행하여 서버를 시작하세요.") 