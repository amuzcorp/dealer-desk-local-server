import os
import sys
import subprocess
import shutil

def build_windows_executable():
    print("Windows 실행 파일 빌드 시작...")
    
    # 빌드 디렉토리 정리
    for dir_to_clean in ["build", "dist"]:
        if os.path.exists(dir_to_clean):
            print(f"{dir_to_clean} 디렉토리 정리 중...")
            shutil.rmtree(dir_to_clean)
    
    # 아이콘 파일 생성 (없는 경우)
    create_icon_file()
    
    # PyInstaller 명령 구성
    pyinstaller_cmd = [
        "pyinstaller",
        "--name=DealerDesk",
        "--windowed",  # GUI 애플리케이션 (콘솔 창 없음)
        "--icon=app_icon.ico",  # 아이콘 파일
        "--add-data=app_icon.ico;.",  # 아이콘 파일을 리소스로 포함
        "--hidden-import=uvicorn.logging",
        "--hidden-import=uvicorn.lifespan.on",
        "--hidden-import=uvicorn.lifespan.off",
        "--hidden-import=pydantic",
        "--hidden-import=sqlalchemy.sql.default_comparator",
        "--hidden-import=email.mime.multipart",
        "--hidden-import=email.mime.text",
        "--hidden-import=email.mime.image",
        "--collect-all=pystray",
        "--collect-all=PIL",
        "--collect-all=sqlalchemy",
        "--collect-all=fastapi",
    ]
    
    # Python 3.13 호환성을 위한 추가 설정
    pyinstaller_cmd.extend([
        "--exclude-module=_bootlocale",  # Python 3.13에서 제거됨
        "--exclude-module=pkg_resources.py2_warn",
    ])
    
    # 필요한 추가 디렉토리와 파일 추가
    for dir_name in ["app", "databases", "Controllers"]:
        if os.path.exists(dir_name):
            pyinstaller_cmd.append(f"--add-data={dir_name};{dir_name}")
    
    for py_file in ["main.py", "web_server.py", "database.py", "schemas.py", 
                   "models.py", "auth_manager.py", "central_socket.py"]:
        if os.path.exists(py_file):
            pyinstaller_cmd.append(f"--add-data={py_file};.")
    
    # 데이터베이스 파일 추가
    for db_file in ["sql_app.db"]:
        if os.path.exists(db_file):
            pyinstaller_cmd.append(f"--add-data={db_file};.")
    
    # 메인 스크립트 추가
    pyinstaller_cmd.append("tray_app.py")
    
    # PyInstaller 실행
    print("PyInstaller 실행 중...")
    print(f"실행 명령: {' '.join(pyinstaller_cmd)}")
    subprocess.run(pyinstaller_cmd, check=True)
    
    # 배포 후 처리
    print("빌드 후 처리 중...")
    dist_dir = os.path.join("dist", "DealerDesk")
    
    # README 생성
    create_readme_file(dist_dir)
    
    print("빌드 완료!")
    print("실행 파일 위치: dist/DealerDesk/DealerDesk.exe")

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

def create_readme_file(dist_dir):
    """배포 디렉토리에 README 파일 생성"""
    readme_path = os.path.join(dist_dir, "README.txt")
    with open(readme_path, "w", encoding="utf-8") as f:
        f.write("""딜러 데스크 트레이 애플리케이션

사용 방법:
1. DealerDesk.exe 파일을 실행합니다.
2. 시스템 트레이에 아이콘이 나타납니다.
3. 트레이 아이콘을 클릭하면 메뉴가 표시됩니다.
4. '서버 시작'을 선택하여 서버를 실행하고 웹 인터페이스를 엽니다.
5. '서버 정지'를 선택하여 서버를 중지합니다.
6. '웹 인터페이스 열기'를 선택하여 브라우저에서 웹 인터페이스를 엽니다.
7. '종료'를 선택하여 애플리케이션을 종료합니다.

참고: 이 애플리케이션은 Python 3.13.2를 기반으로 빌드되었습니다.
""")
    print(f"README 파일이 생성되었습니다: {readme_path}")

if __name__ == "__main__":
    build_windows_executable() 