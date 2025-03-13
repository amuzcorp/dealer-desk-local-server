import os
import subprocess
import sys
import shutil

def install_requirements():
    print("필요한 패키지를 설치하는 중...")
    # 기본 요구 사항
    requirements = [
        "fastapi",
        "uvicorn",
        "sqlalchemy",
        "pyinstaller",
        "python-multipart",
        "websockets",
        "requests",
        "aiohttp"
    ]
    
    for req in requirements:
        subprocess.call([sys.executable, "-m", "pip", "install", req])
    
    # requirements.txt가 있다면 설치
    if os.path.exists("requirements.txt"):
        subprocess.call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])

def build_executable():
    print("실행 파일 빌드 중...")
    
    # PyInstaller 명령어 구성
    pyinstaller_command = [
        "pyinstaller",
        "--name=DealerDeskServer",
        "--onefile",  # 단일 실행 파일로 빌드
        "--noconsole",  # 콘솔 창 숨김 (--console로 변경하면 콘솔 표시)
        "--add-data=templates;templates",  # 템플릿 폴더가 있다면
        "--add-data=static;static",  # 정적 파일 폴더가 있다면
        "--icon=app_icon.ico" if os.path.exists("app_icon.ico") else "",  # 아이콘 파일이 있다면
        "main.py"  # 메인 파일
    ]
    
    # 불필요한 빈 문자열 제거
    pyinstaller_command = [item for item in pyinstaller_command if item]
    
    # PyInstaller 실행
    subprocess.call(pyinstaller_command)
    
    print("빌드 완료!")

def create_launcher():
    print("실행 파일용 배치 스크립트 생성 중...")
    
    with open("run_server.bat", "w") as f:
        f.write("@echo off\n")
        f.write("echo 딜러 데스크 API 서버를 시작합니다...\n")
        f.write("start /b dist\\DealerDeskServer.exe\n")
        f.write("echo 서버가 시작되었습니다. 브라우저에서 http://localhost:3000 으로 접속하세요.\n")
        f.write("pause\n")

def main():
    print("=== 딜러 데스크 API 서버 Windows 빌드 도구 ===")
    
    # 필요한 라이브러리 설치
    install_requirements()
    
    # 실행 파일 빌드
    build_executable()
    
    # 런처 생성
    create_launcher()
    
    print("\n빌드가 완료되었습니다!")
    print("dist 폴더에 DealerDeskServer.exe 파일이 생성되었습니다.")
    print("또는 run_server.bat 파일을 실행하여 서버를 시작할 수 있습니다.")

if __name__ == "__main__":
    main() 