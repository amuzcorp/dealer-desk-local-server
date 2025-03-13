import PyInstaller.__main__
import os
import sys

def build_exe():
    # 현재 디렉토리의 모든 Python 파일 찾기
    python_files = [f for f in os.listdir('.') if f.endswith('.py')]
    
    # 메인 스크립트 경로
    main_script = 'main.py'
    
    # PyInstaller 옵션 설정
    options = [
        main_script,
        '--name=DealerDeskServer',
        '--onefile',
        '--noconsole',
        '--icon=NONE',
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
        '--hidden-import=requests'
        '--hidden-import=sqlalchemy',
        '--hidden-import=cryptography'
        '--collect-all=fastapi',
        '--collect-all=sqlalchemy',
        '--collect-all=cryptography'
    ]
    
    # 모든 Python 파일을 hidden-import로 추가
    # 폴더 순회
    for root, dirs, files in os.walk('.'):
        for file in files:
            if file.endswith('.py'):
                module_name = os.path.splitext(file)[0]
                if module_name != 'main.py' and module_name != 'build.py':
                    options.append(f'--hidden-import={module_name}')
    
    # PyInstaller 실행
    PyInstaller.__main__.run(options)

if __name__ == '__main__':
    build_exe() 