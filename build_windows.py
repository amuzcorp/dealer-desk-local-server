import os
import sys
import subprocess
import shutil
import site
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
    icon_path = 'app_icon.ico'
    if not os.path.exists(icon_path):
        print("아이콘 파일이 없습니다. 기본 아이콘을 사용합니다.")
        icon_path = None
    
    # 필요한 디렉토리 확인
    data_dirs = []
    if os.path.exists('templates'):
        data_dirs.append(('templates', 'templates'))
    if os.path.exists('static'):
        data_dirs.append(('static', 'static'))
    
    # 데이터베이스 파일 확인
    db_files = glob.glob('*.db')
    for db_file in db_files:
        data_dirs.append((db_file, '.'))
    
    # .env 파일 확인
    if os.path.exists('.env'):
        data_dirs.append(('.env', '.'))
    
    # PyInstaller 명령어 구성
    cmd = [
        'pyinstaller',
        '--noconfirm',
        '--clean',
        '--name=DealerDesk',
        '--onedir',  # 디렉토리로 출력
    ]
    
    # 아이콘 추가
    if icon_path:
        cmd.append(f'--icon={icon_path}')
    
    # 데이터 파일 추가
    for src, dst in data_dirs:
        cmd.append(f'--add-data={src};{dst}')
    
    # 필요한 모듈 추가
    hidden_imports = [
        'uvicorn.logging',
        'uvicorn.loops',
        'uvicorn.loops.auto',
        'uvicorn.protocols',
        'uvicorn.protocols.http',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.websockets',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.lifespan',
        'uvicorn.lifespan.on',
        'fastapi',
        'starlette',
        'pydantic',
        'sqlalchemy',
        'websockets',
        'pystray._win32',
        'PIL._tkinter_finder',
        'email.mime.multipart',
        'email.mime.text',
        'email.mime.image',
    ]
    
    for imp in hidden_imports:
        cmd.append(f'--hidden-import={imp}')
    
    # 콘솔 숨기기
    cmd.append('--noconsole')
    
    # 실행 파일 지정
    cmd.append('tray_app.py')
    
    # 명령어 출력
    print("실행할 명령어:")
    print(" ".join(cmd))
    
    # PyInstaller 실행
    try:
        print("PyInstaller 실행 중...")
        result = subprocess.run(cmd, check=True)
        print(f"PyInstaller 종료 코드: {result.returncode}")
        
        if result.returncode == 0:
            print("\n빌드가 성공적으로 완료되었습니다!")
            print("실행 파일은 dist/DealerDesk 디렉토리에 있습니다.")
            
            # 실행 파일 경로
            exe_path = os.path.abspath(os.path.join('dist', 'DealerDesk', 'DealerDesk.exe'))
            print(f"실행 파일 경로: {exe_path}")
            
            # 바로가기 생성
            try:
                desktop_path = os.path.join(os.path.expanduser("~"), "Desktop")
                shortcut_path = os.path.join(desktop_path, "DealerDesk.lnk")
                
                if os.path.exists(desktop_path):
                    print(f"바탕화면에 바로가기 생성 중: {shortcut_path}")
                    
                    # Windows 전용 바로가기 생성 코드
                    try:
                        import win32com.client
                        shell = win32com.client.Dispatch("WScript.Shell")
                        shortcut = shell.CreateShortCut(shortcut_path)
                        shortcut.Targetpath = exe_path
                        shortcut.WorkingDirectory = os.path.dirname(exe_path)
                        shortcut.IconLocation = exe_path
                        shortcut.save()
                        print("바로가기가 생성되었습니다.")
                    except ImportError:
                        print("pywin32 모듈이 설치되지 않아 바로가기를 생성할 수 없습니다.")
                        print("바로가기를 수동으로 생성하세요.")
            except Exception as e:
                print(f"바로가기 생성 중 오류 발생: {e}")
        else:
            print("\n빌드 중 오류가 발생했습니다.")
    except subprocess.CalledProcessError as e:
        print(f"\n빌드 실패: {e}")
    except Exception as e:
        print(f"\n예상치 못한 오류 발생: {e}")

if __name__ == "__main__":
    build_windows_exe() 