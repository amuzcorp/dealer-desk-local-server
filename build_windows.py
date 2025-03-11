import os
import sys
import subprocess
import shutil
import glob

def build_windows_exe():
    print("윈도우용 Dealer Desk 빌드를 시작합니다...")
    
    # 빌드 디렉토리 정리
    if os.path.exists('build'):
        print("기존 build 디렉토리 삭제 중...")
        shutil.rmtree('build', ignore_errors=True)
    if os.path.exists('dist'):
        print("기존 dist 디렉토리 삭제 중...")
        shutil.rmtree('dist', ignore_errors=True)
    
    # 아이콘 파일 확인
    icon_option = ""
    if os.path.exists('app_icon.ico'):
        icon_option = "--icon=app_icon.ico"
        print("아이콘 파일을 찾았습니다.")
    else:
        print("아이콘 파일이 없습니다. 기본 아이콘을 사용합니다.")
    
    # 데이터 파일 옵션 구성
    data_options = []
    if os.path.exists('templates'):
        data_options.append("--add-data=templates;templates")
    if os.path.exists('static'):
        data_options.append("--add-data=static;static")
    
    # 데이터베이스 파일 추가
    for db_file in glob.glob('*.db'):
        data_options.append(f"--add-data={db_file};.")
    
    # .env 파일 추가
    if os.path.exists('.env'):
        data_options.append("--add-data=.env;.")
    
    # PyInstaller 명령어 구성
    cmd = f"""
    pyinstaller --noconfirm --clean --name=DealerDesk {icon_option} --onedir --noconsole ^
    --hidden-import=uvicorn.logging ^
    --hidden-import=uvicorn.loops ^
    --hidden-import=uvicorn.loops.auto ^
    --hidden-import=uvicorn.protocols ^
    --hidden-import=uvicorn.protocols.http ^
    --hidden-import=uvicorn.protocols.http.auto ^
    --hidden-import=uvicorn.protocols.websockets ^
    --hidden-import=uvicorn.protocols.websockets.auto ^
    --hidden-import=uvicorn.lifespan ^
    --hidden-import=uvicorn.lifespan.on ^
    --hidden-import=fastapi ^
    --hidden-import=starlette ^
    --hidden-import=pydantic ^
    --hidden-import=sqlalchemy ^
    --hidden-import=websockets ^
    --hidden-import=pystray._win32 ^
    --hidden-import=PIL._tkinter_finder ^
    {' '.join(data_options)} ^
    tray_app.py
    """
    
    # 명령어 출력
    print("\n실행할 명령어:")
    print(cmd)
    
    # 배치 파일 생성
    with open('build_app.bat', 'w') as f:
        f.write(cmd)
    
    print("\n빌드 배치 파일이 생성되었습니다: build_app.bat")
    print("이 파일을 윈도우에서 실행하여 애플리케이션을 빌드하세요.")
    
    # 윈도우 환경인 경우 바로 실행
    if sys.platform.startswith('win'):
        print("\n윈도우 환경이 감지되었습니다. 빌드를 시작합니다...")
        try:
            subprocess.run('build_app.bat', shell=True, check=True)
            print("\n빌드가 완료되었습니다!")
            print("실행 파일은 dist/DealerDesk 디렉토리에 있습니다.")
        except subprocess.CalledProcessError as e:
            print(f"\n빌드 실패: {e}")
    else:
        print("\n현재 윈도우 환경이 아닙니다.")
        print("윈도우 환경에서 build_app.bat 파일을 실행하세요.")

if __name__ == "__main__":
    build_windows_exe() 