import os
import sys
import subprocess
import shutil
import time
import traceback
import ctypes
import stat

def is_admin():
    """Windows에서 관리자 권한 확인"""
    try:
        return ctypes.windll.shell32.IsUserAnAdmin() != 0
    except:
        return False

def force_delete(file_path):
    """파일 강제 삭제 (잠금 해제 시도)"""
    try:
        if os.path.exists(file_path):
            # 파일 속성 변경 시도
            os.chmod(file_path, stat.S_IWRITE)
            # 삭제 시도
            os.unlink(file_path)
            return True
    except Exception as e:
        print(f"파일 강제 삭제 실패: {file_path}, 오류: {str(e)}")
        return False

def kill_processes_by_name(process_names):
    """지정된 이름의 프로세스 종료 (Windows)"""
    for name in process_names:
        try:
            subprocess.run(f"taskkill /f /im {name}", shell=True, check=False)
            print(f"{name} 프로세스 종료 시도")
        except Exception as e:
            print(f"{name} 프로세스 종료 실패: {str(e)}")

def clean_directory(dir_path, retry=3, sleep_time=1):
    """디렉토리 정리 (재시도 로직 포함)"""
    if not os.path.exists(dir_path):
        return
    
    print(f"{dir_path} 디렉토리 정리 중...")
    
    for attempt in range(retry):
        try:
            # 먼저 모든 파일의 쓰기 권한 활성화 시도
            for root, dirs, files in os.walk(dir_path):
                for file in files:
                    file_path = os.path.join(root, file)
                    try:
                        os.chmod(file_path, stat.S_IWRITE)
                    except:
                        pass
            
            # 디렉토리 삭제 시도
            shutil.rmtree(dir_path)
            print(f"{dir_path} 삭제 성공")
            return True
        except Exception as e:
            print(f"{dir_path} 삭제 시도 {attempt+1}/{retry} 실패: {str(e)}")
            if attempt < retry - 1:
                print(f"{sleep_time}초 후 재시도...")
                time.sleep(sleep_time)
    
    print(f"경고: {dir_path} 삭제 실패, 파일 접근 문제가 있을 수 있습니다.")
    return False

def wait_for_user_confirmation(message="계속하려면 아무 키나 누르세요..."):
    """사용자 확인 대기"""
    print(message)
    input()

def create_icon_file():
    """간단한 아이콘 파일이 없는 경우 생성"""
    if not os.path.exists("app_icon.ico"):
        try:
            from PIL import Image
            
            print("아이콘 파일 생성 중...")
            # 간단한 파란색 아이콘 생성
            img = Image.new('RGB', (256, 256), color=(66, 133, 244))
            img.save('app_icon.png')
            
            # .ico 파일로 변환
            img.save('app_icon.ico')
            print("아이콘 파일이 생성되었습니다.")
        except Exception as e:
            print(f"아이콘 생성 중 오류 발생: {str(e)}")
            print("기본 아이콘으로 계속 진행합니다.")

def build_windows_executable():
    print("\n" + "="*80)
    print("Windows 실행 파일 빌드 시작...")
    print("="*80 + "\n")
    
    # 관리자 권한 확인
    if not is_admin():
        print("경고: 관리자 권한으로 실행되지 않았습니다. 파일 접근 문제가 발생할 수 있습니다.")
        print("관리자 권한으로 다시 실행하는 것을 권장합니다.")
        wait_for_user_confirmation("계속 진행하려면 Enter 키를 누르세요...")
    
    # 실행 중인 관련 프로세스 종료
    print("빌드 전 관련 프로세스 종료 중...")
    kill_processes_by_name([
        "DealerDesk.exe",
        "uvicorn.exe",
    ])
    
    # 잠시 대기하여 프로세스가 완전히 종료되도록 함
    time.sleep(2)
    
    # 빌드 디렉토리 정리
    for dir_to_clean in ["build", "dist"]:
        clean_directory(dir_to_clean)
    
    # 아이콘 파일 생성 (없는 경우)
    create_icon_file()
    
    # 명시적 작업 디렉토리 생성
    work_dir = os.path.join(os.getcwd(), "build", "work")
    os.makedirs(work_dir, exist_ok=True)
    
    # PyInstaller 명령 구성
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=DealerDesk",
        "--windowed",  # GUI 애플리케이션 (콘솔 창 없음)
        "--icon=app_icon.ico",  # Windows 아이콘 파일
        "--workpath=" + work_dir,  # 작업 디렉토리 명시적 지정
        "--noconfirm",  # 확인 없이 진행
        "--clean",  # 빌드 전 정리
        "--log-level=DEBUG",  # 디버그 로그 활성화
        "--add-data=app_icon.ico;.",  # 아이콘 파일을 리소스로 포함
    ]
    
    # Python 3.13 호환성을 위한 imports 추가
    hidden_imports = [
        "uvicorn.logging",
        "uvicorn.lifespan.on",
        "uvicorn.lifespan.off",
        "pydantic",
        "sqlalchemy.sql.default_comparator",
        "email.mime.multipart",
        "email.mime.text",
        "email.mime.image",
        "fastapi.middleware",
        "fastapi.middleware.cors",
        "fastapi.responses",
        "starlette.middleware",
        "starlette.middleware.cors",
        "starlette.responses",
        "tkinter",
        "tkinter.ttk",
        "tkinter.scrolledtext",
        "tkinter.messagebox",
        "tkinter.filedialog",
        "fastapi",
        "starlette",
        "asyncio",
        "aiohttp",
        "logging.handlers",
        "encodings.idna",
    ]
    
    for imp in hidden_imports:
        pyinstaller_cmd.append(f"--hidden-import={imp}")
    
    # 필수 모듈 수집
    collect_modules = [
        "pystray",
        "PIL",
        "sqlalchemy",
        "fastapi",
        "starlette",
        "uvicorn",
        "tkinter",
        "aiohttp",
    ]
    
    for mod in collect_modules:
        pyinstaller_cmd.append(f"--collect-all={mod}")
    
    # Python 3.13 호환성을 위한 추가 설정
    pyinstaller_cmd.extend([
        "--exclude-module=_bootlocale",  # Python 3.13에서 제거됨
        "--exclude-module=pkg_resources.py2_warn",
    ])
    
    # 디렉토리 복사 설정
    for dir_name in ["app", "databases", "Controllers"]:
        if os.path.exists(dir_name):
            pyinstaller_cmd.append(f"--add-data={dir_name};{dir_name}")
    
    # 파일 복사 설정
    copy_files = [
        "main.py", 
        "web_server.py", 
        "database.py", 
        "schemas.py", 
        "models.py", 
        "auth_manager.py", 
        "central_socket.py",
        "sql_app.db",
    ]
    
    for py_file in copy_files:
        if os.path.exists(py_file):
            pyinstaller_cmd.append(f"--add-data={py_file};.")
    
    # 메인 스크립트 추가
    pyinstaller_cmd.append("tray_app.py")
    
    # PyInstaller 실행
    print("\n" + "-"*80)
    print("PyInstaller 실행 중...")
    print(f"실행 명령: {' '.join(pyinstaller_cmd)}")
    print("-"*80 + "\n")
    
    try:
        subprocess.run(pyinstaller_cmd, check=True)
        print("PyInstaller 빌드 완료!")
    except subprocess.CalledProcessError as e:
        print(f"PyInstaller 실행 중 오류 발생: {e}")
        print("직접 필요한 파일 복사를 시도합니다...")
        manual_copy_files()
    
    # 배포 후 처리
    print("빌드 후 처리 중...")
    dist_dir = os.path.join("dist", "DealerDesk")
    
    # README 생성
    create_readme_file(dist_dir)
    
    # _internal 디렉토리 확인
    check_internal_dir(dist_dir)
    
    # 관리자 권한으로 실행하는 배치 파일 생성
    create_batch_launcher(dist_dir)
    
    print("\n" + "="*80)
    print("빌드 완료!")
    print("실행 파일 위치: dist/DealerDesk/DealerDesk.exe")
    print("="*80)

def manual_copy_files():
    """PyInstaller가 실패한 경우 수동으로 필요한 파일 복사"""
    print("\n" + "-"*80)
    print("수동으로 파일 복사 시작...")
    print("-"*80)
    
    # 기본 디렉토리 구조 생성
    dist_dir = os.path.join("dist", "DealerDesk")
    internal_dir = os.path.join(dist_dir, "_internal")
    
    os.makedirs(dist_dir, exist_ok=True)
    os.makedirs(internal_dir, exist_ok=True)
    
    # 핵심 파일 복사
    copy_files = [
        "main.py", 
        "web_server.py", 
        "database.py", 
        "schemas.py", 
        "models.py", 
        "auth_manager.py", 
        "central_socket.py",
        "tray_app.py",
        "sql_app.db",
        "app_icon.ico",
    ]
    
    for file in copy_files:
        if os.path.exists(file):
            dest_path = os.path.join(internal_dir, file)
            print(f"복사 중: {file} -> {dest_path}")
            try:
                shutil.copy2(file, dest_path)
            except Exception as e:
                print(f"파일 복사 실패: {file}, 오류: {str(e)}")
    
    # 디렉토리 복사
    for dir_name in ["app", "databases", "Controllers"]:
        if os.path.exists(dir_name):
            dest_dir = os.path.join(internal_dir, dir_name)
            print(f"디렉토리 복사 중: {dir_name} -> {dest_dir}")
            try:
                shutil.copytree(dir_name, dest_dir, dirs_exist_ok=True)
            except Exception as e:
                print(f"디렉토리 복사 실패: {dir_name}, 오류: {str(e)}")
    
    print("수동 파일 복사 완료")

def check_internal_dir(dist_dir):
    """_internal 디렉토리가 존재하는지 확인하고 없으면 생성"""
    internal_dir = os.path.join(dist_dir, "_internal")
    
    if not os.path.exists(internal_dir):
        print("_internal 디렉토리가 없습니다. 수동으로 생성합니다...")
        os.makedirs(internal_dir, exist_ok=True)
        
        # 필요한 파일이 있는지 확인하고 복사
        manual_copy_files()
    else:
        print(f"_internal 디렉토리 확인 완료: {internal_dir}")
        # _internal 디렉토리 내용 출력
        print("_internal 디렉토리 내용:")
        try:
            for item in os.listdir(internal_dir):
                item_path = os.path.join(internal_dir, item)
                if os.path.isdir(item_path):
                    print(f"  - {item}/ (디렉토리)")
                else:
                    print(f"  - {item}")
        except Exception as e:
            print(f"_internal 디렉토리 내용 확인 중 오류: {str(e)}")

def create_readme_file(dist_dir):
    """배포 디렉토리에 README 파일 생성"""
    readme_path = os.path.join(dist_dir, "README.txt")
    try:
        with open(readme_path, "w", encoding="utf-8") as f:
            f.write("""딜러 데스크 트레이 애플리케이션 (Windows 버전)

사용 방법:
1. DealerDesk.exe 파일을 실행합니다. (관리자 권한이 필요할 수 있습니다)
2. 시스템 트레이에 아이콘이 나타납니다.
3. 트레이 아이콘을 클릭하면 메뉴가 표시됩니다.
4. '서버 시작'을 선택하여 서버를 실행하고 웹 인터페이스를 엽니다.
5. '서버 정지'를 선택하여 서버를 중지합니다.
6. '웹 인터페이스 열기'를 선택하여 브라우저에서 웹 인터페이스를 엽니다.
7. '로그' 메뉴에서 트레이 앱과 런처의 로그를 확인할 수 있습니다.
8. '종료'를 선택하여 애플리케이션을 종료합니다.

문제 해결:
- 접근 거부 오류가 발생한다면 Run_As_Admin.bat 파일을 사용하여 관리자 권한으로 실행하세요.
- 서버 시작 문제는 로그 파일을 확인하세요.
- Windows 보안 경고가 표시될 경우, '추가 정보'를 클릭한 다음 '실행'을 선택하세요.

참고: 이 애플리케이션은 Python 3.13을 기반으로 빌드되었습니다.
""")
        print(f"README 파일이 생성되었습니다: {readme_path}")
    except Exception as e:
        print(f"README 파일 생성 실패: {str(e)}")

def create_batch_launcher(dist_dir):
    """관리자 권한으로 실행하는 배치 파일 생성"""
    batch_path = os.path.join(dist_dir, "Run_As_Admin.bat")
    try:
        with open(batch_path, "w", encoding="utf-8") as f:
            f.write("""@echo off
echo 딜러 데스크 트레이 애플리케이션을 관리자 권한으로 실행합니다...
powershell -Command "Start-Process -FilePath '%~dp0DealerDesk.exe' -Verb RunAs"
exit
""")
        print(f"관리자 권한 실행 배치 파일 생성: {batch_path}")
    except Exception as e:
        print(f"배치 파일 생성 실패: {str(e)}")

if __name__ == "__main__":
    try:
        build_windows_executable()
    except Exception as e:
        print(f"빌드 중 예상치 못한 오류 발생: {str(e)}")
        traceback.print_exc()
        wait_for_user_confirmation("오류가 발생했습니다. 종료하려면 Enter 키를 누르세요...")
        sys.exit(1) 