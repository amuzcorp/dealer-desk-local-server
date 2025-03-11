import os
import sys
import subprocess
import shutil

def build_windows_exe():
    # 빌드 디렉토리 생성
    if not os.path.exists('build'):
        os.makedirs('build')
    if not os.path.exists('dist'):
        os.makedirs('dist')

    # PyInstaller 명령어 실행
    subprocess.run([
        'pyinstaller',
        '--noconfirm',
        '--clean',
        '--name=DealerDesk',
        '--icon=app_icon.ico',  # 아이콘 파일이 있다면 사용
        '--add-data=templates;templates',  # 템플릿 디렉토리가 있다면
        '--add-data=static;static',  # 정적 파일 디렉토리가 있다면
        '--hidden-import=uvicorn.logging',
        '--hidden-import=uvicorn.loops',
        '--hidden-import=uvicorn.loops.auto',
        '--hidden-import=uvicorn.protocols',
        '--hidden-import=uvicorn.protocols.http',
        '--hidden-import=uvicorn.protocols.http.auto',
        '--hidden-import=uvicorn.protocols.websockets',
        '--hidden-import=uvicorn.protocols.websockets.auto',
        '--hidden-import=uvicorn.lifespan',
        '--hidden-import=uvicorn.lifespan.on',
        '--hidden-import=fastapi',
        '--hidden-import=starlette',
        '--hidden-import=pydantic',
        '--hidden-import=sqlalchemy',
        '--hidden-import=websockets',
        '--noconsole',  # GUI 모드로 실행
        'tray_app.py'
    ])

    print("빌드가 완료되었습니다.")
    print("실행 파일은 dist/DealerDesk 디렉토리에 있습니다.")

if __name__ == "__main__":
    build_windows_exe() 